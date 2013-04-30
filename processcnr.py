#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Imports IP history data from Cisco Network Registrar to aggregated database"""

# Copyright 2013 Sergej Alikov

# This file is part of IPhistdb.

# IPhistdb is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# IPhistdb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with IPhistdb.  If not, see <http://www.gnu.org/licenses/>.


# Run this file daily on the CNR server

import os
import sys
import csv
import logging
import logging.config
import ConfigParser
from subprocess import PIPE, Popen
import datetime
import pytz
import re
import smtplib
from email.mime.text import MIMEText
import pymysql
pymysql.install_as_MySQLdb()
from iphistdb.aggdb import AggDB
from iphistdb.histdb import IPLease


class LockfileException(Exception):
    pass


class CNRException(Exception):
    pass


class ParseException(CNRException):
    pass


class Config:
    def __init__(self, filename):
        self._cfg = ConfigParser.ConfigParser()
        self._cfg.read(filename)

        self.get = self._cfg.get

    def getpath(self, section, option):
        return os.path.expandvars(self._cfg.get(section, option))


class CnrCmd:
    def __init__(self, path, user, passwd):
        self._path = path
        self._user = user
        self._passwd = passwd

    def _parse_cnr_timestamp(self, timestamp):
        """
        Converts date string of form 'month/day/year hour:minute:seconds'
        into datetime object
        """
        ts = datetime.datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')
        return pytz.utc.localize(ts)

    def _parse_cnr_mac(self, mac):
        """
        Converts MAC address of form '1,6,00:de:ad:be:ef:00' into
        '00deadbeef00'
        """
        return mac.replace(':', '').split(',')[-1]


class Iphist(CnrCmd):

    def leases(self, ip, start=None, end=None):
        """
        Queries CNR iphistory database and yields IPLease objects

        Args:
        ip: IP address or 'all'
        start: Start date of the lease of type datetime
        end: End date of the lease of type datetime

        Raises:
        CNRException,
        UnknownStateException
        """

        format = 'address,'\
                 'client-mac-addr,'\
                 'relay-agent-circuit-id,'\
                 'relay-agent-remote-id,'\
                 'start-time-of-state,'\
                 'expiration,'\
                 'state'

        args = []
        args.append(self._path)
        args.extend(['-N', self._user])
        args.extend(['-P', self._passwd])
        args.extend(['-f', format])
        args.append(ip)
        if start is not None:
            args.append(start.strftime('%m/%d/%Y %H:%M:%S'))
        if end is not None:
            args.append(end.strftime('%m/%d/%Y %H:%M:%S'))

        proc = Popen(args, stdout=PIPE, stderr=PIPE)

        parser = csv.reader(proc.stdout)

        for row in parser:

            if len(row) < 7:
                raise ParseException(row)

            if row[6] == 'leased':
                lease = IPLease(row[0])
                lease.lease(self._parse_cnr_mac(row[1]),
                            self._parse_cnr_timestamp(row[4]),
                            None,
                            row[2],
                            row[3],
                            '0.0.0.0')

                lease.free(self._parse_cnr_timestamp(row[5]))

                yield lease

            elif row[6] == 'expired':
                pass
            elif row[6] == 'available':
                pass
            elif row[6] == 'offered':
                pass
            elif row[6] == 'unavailable':
                pass
            else:
                raise ParseException(row)

        err = proc.stderr.read()
        if len(err) > 0:
            raise CNRException(err)


class Nrcmd(CnrCmd):

    def execute(self, cmd):
        wd = os.path.realpath(os.path.dirname(self._path))
        args = []
        args.append(self._path)
        args.extend(['-N', self._user])
        args.extend(['-P', self._passwd])
        args.append(cmd)

        # Of course we can run nrcmd -b here an do full 2-way comm
        # but I doubt it is needed in this case
        proc = Popen(args, stdout=PIPE, stderr=PIPE, cwd=wd)

        output = proc.stdout.read().splitlines()
        if len(output) == 0:
            raise CNRException('Empty output')

        err = proc.stderr.read()
        if len(err) > 0:
            raise CNRException(err)

        status_code, status_text = re.split(r'\W', output[0], 1)

        if int(status_code) > 199:
            raise CNRException(' '.join([output[0]]))

        if len(output) > 1:
            data = output[1:]
        else:
            data = []

        return (int(status_code), status_text), data

    def dhcp_reload(self):
        return self.execute('dhcp reload')

    def dhcp_trimIPHistory(self, days):
        return self.execute(''.join(['dhcp trimIPHistory -', str(days), 'd']))


def sendmail(smtp, mailfrom, mailto, subject, msg):
    msg = MIMEText(msg)
    msg['Subject'] = subject
    msg['From'] = mailfrom
    msg['To'] = mailto
    smtp = smtplib.SMTP(smtp)
    smtp.sendmail(mailfrom, mailto, msg.as_string())
    smtp.quit()


def lock(filename):
    if os.path.isfile(filename):
        raise LockfileException('Another instance is still running!')
    else:
        f = open(filename, 'w+')
        f.close()


def unlock(filename):
    os.remove(filename)


def main(argv):

    if os.name == 'nt':
        cfgpath = os.path.expandvars('%APPDATA%\IPhistdb')
    elif os.name == 'posix':
        cfgpath = '/etc/IPhistdb'

    cfg = Config(os.path.join(cfgpath, 'processcnr.ini'))

    logging.config.fileConfig(os.path.join(cfgpath, 'processcnr.logging.ini'))
    logger = logging.getLogger('file')

    logger.debug('INIT')

    try:
        lock(cfg.getpath('App', 'lockfile'))

        try:

            db = AggDB()
            db.connect(cfg.get('AggDB', 'host'),
                       cfg.get('AggDB', 'user'),
                       cfg.get('AggDB', 'pass'),
                       cfg.get('AggDB', 'db'))

            iphist = Iphist(cfg.get('CNR', 'iphist'),
                            cfg.get('CNR', 'user'),
                            cfg.get('CNR', 'pass'))

            for lease in iphist.leases('all'):
                try:
                    db.addlease(lease)
                    logger.debug(' '.join(['addlease',
                                           lease.ip,
                                           lease.start.strftime('%Y-%m-%d %H:%M:%S'),
                                           lease.end.strftime('%Y-%m-%d %H:%M:%S')]))
                except ParseException as e:
                    logger.warning(e)

            nrcmd = Nrcmd(cfg.get('CNR', 'nrcmd'),
                          cfg.get('CNR', 'user'),
                          cfg.get('CNR', 'pass'))

            nrcmd.dhcp_trimIPHistory(cfg.get('CNR', 'keep_history_days'))
            logger.debug('dhcp trimIPhistory')
            nrcmd.dhcp_reload()
            logger.debug('dhcp reload')

        finally:
            unlock(cfg.getpath('App', 'lockfile'))
    except:
        e = sys.exc_info()[1]
        sendmail(cfg.get('SMTP', 'smtp'),
                 cfg.get('SMTP', 'from'),
                 cfg.get('SMTP', 'to'),
                 'CNR iphistory importer errors',
                 str(e))
        raise

    logger.debug('DONE')


if __name__ == "__main__":
    main(sys.argv[1:])
