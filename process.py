#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Imports IP history data from dhcpd logs to histdb MySQL database"""

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


# Add this file to cron.daily or cron.d or logrotate.d script (see INSTALL)

import sys
import os
import ConfigParser
import logging
import datetime
from histdb import DBException, HistDB
import re
import pytz


config_filename = "/etc/IPhistdb/config.ini"


class HistFileImporter:

    def __init__(self, config):
        self._db = HistDB()

        self._cfg = ConfigParser.ConfigParser()
        self._cfg.read(config)

        self.timezone = pytz.timezone(self._cfg.get("App", "timezone"))

        self._logger = logging.getLogger("process")

        loglevels = {"NOTSET": logging.NOTSET, "DEBUG": logging.DEBUG,
                     "INFO": logging.INFO, "WARNING": logging.WARNING,
                     "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}

        self._logger.setLevel(loglevels[self._cfg.get("Logging", "level")])

        fh = logging.FileHandler(filename=self._cfg.get("Logging", "logfile"))

        lformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        fh.setFormatter(logging.Formatter(lformat))

        self._logger.addHandler(fh)

        self._db.connect(self._cfg.get("MySQL", "host"),
                         self._cfg.get("MySQL", "user"),
                         self._cfg.get("MySQL", "pass"),
                         self._cfg.get("MySQL", "db"))

        self._logger.debug("init")

    def add(self, filenames):
        """Add file(s) to database"""
        self._db.addfiles(filenames)
        self._logger.debug("add" + " ".join(filenames))

    def remove(self, filename):
        """Remove file from database"""
        self._db.removefile(filename)
        self._logger.warning(" ".join(["remove", filename]))

    def process(self):
        """Process unprocessed files and import parsed data to database"""
        for logfile in self._db.get_unprocessed_files():
            try:
                self.parse(logfile)
            except IOError:
                self.remove(logfile)
        self._logger.debug("process")

    def _tidy_dhcpd_hexstring(self, hexstr):
        """Take hex-encoded string in form a:bc:de:f
        and transform it to 0abcde0f"""
        return "".join(map(lambda x: x.rjust(2, "0"), hexstr.split(":")))

    def _parse_syslog_timestamp(self, timestamp, year=None):
        """Parses Syslog format timestamps (Example: "Jan 16 13:12:24")"""

        now = datetime.datetime.now()

        if year is None:
            current_year = now.year
        else:
            current_year = year

        full_date = " ".join([str(current_year), timestamp])

        ts = datetime.datetime.strptime(full_date, "%Y %b %d %H:%M:%S")

        # Date has to be in the past:
        if ts <= now:
            return ts
        else:
            return self._parse_syslog_timestamp(timestamp, current_year - 1)

    def _hexstring2printable(self, hexstr):
        """Outputs printable version of string"""

        hs = self._tidy_dhcpd_hexstring(hexstr)
        return hs.decode("hex").encode("string_escape")

    def _parse_leasecommit(self, parts):
        ts = self._parse_syslog_timestamp(" ".join(parts[0:3]))
        utc_ts = self.timezone.localize(ts).astimezone(pytz.utc)
        # Always store time in UTC
        timestamp = utc_ts.strftime("%Y-%m-%d %H:%M:%S")
        ip_addr = parts[6]
        mac_addr = self._tidy_dhcpd_hexstring(parts[7])
        circuit_id = self._hexstring2printable(parts[8])
        remote_id = self._hexstring2printable(parts[9])
        giaddr = parts[10]
        lease_time = int(self._tidy_dhcpd_hexstring(parts[11]), 16)

        try:
            self._db.add_history_record(timestamp, ip_addr, mac_addr,
                                        circuit_id, remote_id, giaddr,
                                        lease_time, "LEASED")
        except DBException as e:
            self._logger.warning(e)

    def _parse_leasefree(self, parts):
        ts = self._parse_syslog_timestamp(" ".join(parts[0:3]))
        utc_ts = self.timezone.localize(ts).astimezone(pytz.utc)
        # Always store time in UTC
        timestamp = utc_ts.strftime("%Y-%m-%d %H:%M:%S")
        ip_addr = parts[6]

        try:
            self._db.add_history_record(timestamp, ip_addr, None,
                                        None, None, None, None, "FREE")
        except DBException as e:
            self._logger.warning(e)

    def parse(self, logfile):
        """Parse file and import data to database"""
        with open(logfile, "r") as f:
            for line in f:

                parts = re.split("\s+", line.rstrip("\n"))

                if len(parts) > 4:
                    if parts[5] == "LEASECOMMIT":
                        self._parse_leasecommit(parts)
                    if parts[5] == "LEASERELEASE":
                        self._parse_leasefree(parts)
                    if parts[5] == "LEASEEXPIRY":
                        self._parse_leasefree(parts)

        self._db.mark_as_processed(logfile)
        self._logger.debug(" ".join(["parse", logfile]))


def main(argv):

    h = HistFileImporter(config_filename)

    if len(argv) > 0:

        h.add(filter(os.path.isfile, argv))

    h.process()


if __name__ == "__main__":
    main(sys.argv[1:])
