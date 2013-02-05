# -*- coding: utf-8 -*-

"""histdb related functions"""

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

import MySQLdb
from MySQLdb.constants import ER
from datetime import timedelta


class DBException(Exception):
    pass


class HistDB:

    def connect(self, host, user, passwd, db):
        self._conn = MySQLdb.connect(host=host, user=user,
                                     passwd=passwd, db=db)

    def addfiles(self, filenames):
        c = self._conn.cursor()
        try:
            # As we are inserting multiple values here -
            # "ON DUPLICATE KEY" construction is needed, so
            # failure of the one INSERT doesn't affect others
            q = "INSERT INTO files (filename) VALUES (%s) " \
                "ON DUPLICATE KEY UPDATE filename=VALUES(filename)"
            c.executemany(q, filenames)
            self._conn.commit()
        finally:
            c.close()

    def removefile(self, filename):
        c = self._conn.cursor()
        try:
            q = "DELETE FROM files WHERE filename=%s"
            c.execute(q, filename)
            self._conn.commit()
        finally:
            c.close()

    def get_unprocessed_files(self):
        c = self._conn.cursor()
        try:
            q = "SELECT filename FROM files WHERE processed IS NULL"
            c.execute(q)
            result = map(lambda x: x[0], c.fetchall())
        finally:
            c.close()

        return result

    def mark_as_processed(self, filename):
        """
        Marks <filename> as processed by writing current date
        into `processed` column
        """
        c = self._conn.cursor()
        try:
            q = "UPDATE files SET processed=NOW() WHERE filename=%s"
            c.execute(q, [filename])
            self._conn.commit()
        finally:
            c.close()

    def add_history_record(self, timestamp, ip_addr, mac_addr, circuit_id,
                           remote_id, giaddr, lease_time, state):
        c = self._conn.cursor()
        try:
            q = "INSERT INTO history " \
                "(timestamp, ip, mac, circuit_id, remote_id, giaddr, " \
                "lease_time, state) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

            c.execute(q, [timestamp, ip_addr, mac_addr, circuit_id,
                      remote_id, giaddr, lease_time, state])
            self._conn.commit()

        except MySQLdb.IntegrityError as e:
            if e.args[0] == ER.DUP_ENTRY:
                raise DBException(e.args)
            else:
                raise
            pass
        finally:
            c.close()

    def del_history_records(self, row_ids):
        """
        Deletes records with specified ids from history table
        """
        c = self._conn.cursor()
        try:
            q = "DELETE FROM history WHERE id_history=%s"

            c.executemany(q, row_ids)
            self._conn.commit()

        finally:
            c.close()

    def aggregate_history(self, ip=None):
        """
        Aggregates multiple records into leases and emits them via yield.
        The memory usage should be fairly low even for huge number
        of records.

        Aggregation may be done for the specified <ip> address or for all
        records in table.
        """
        leases = IPLeases()

        c = self._conn.cursor()

        try:
            if ip == None:
                q = "SELECT ip, mac, timestamp, lease_time, circuit_id, " \
                    "remote_id, giaddr, state, id_history " \
                    "FROM history ORDER BY timestamp ASC"
            else:
                q = "SELECT ip, mac, timestamp, lease_time, circuit_id, " \
                    "remote_id, giaddr, state, id_history " \
                    "FROM history WHERE ip=%s ORDER BY timestamp ASC"

            c.arraysize = 16
            c.execute(q, [ip])
            while True:
                records = c.fetchmany()
                if len(records) == 0:
                    break

                for record in records:
                    ip = record[0]
                    state = record[7]

                    lease = leases.add(ip)

                    if state == "LEASED":
                        lease.lease(record[1], record[2], record[3],
                                    record[4], record[5], record[6])

                    if state == "FREE":
                        lease.free(record[2])

                    lease.add_sqlrow(record[8])

                    if lease.complete:
                        yield lease
                        lease.reset()

            # Emit open leases
            for key, lease in leases.all().iteritems():
                if not lease.new and not lease.complete:
                    lease.free()
                    yield lease

        finally:
            c.close()

    def cleanup(self, days=183):
        """
        Removes filenames from DB, which have been processed <days> ago
        Defaults to half-year
        """
        c = self._conn.cursor()
        try:
            q = "DELETE from files WHERE processed < NOW() - INTERVAL %s DAY"
            c.execute(q, [days])
            self._conn.commit()
        finally:
            c.close()


class IPLeases:
    def __init__(self):
        self._leases = {}

    def add(self, ip):
        if ip not in self._leases:
            self._leases[ip] = IPLease(ip)
        return self._leases[ip]

    def all(self):
        return self._leases


class IPLease:
    def __init__(self, ip):
        self.reset()
        self.ip = ip

    def lease(self, mac, timestamp, lease_time, circuit_id, remote_id,
              giaddr):
        if self.new:
            self.mac = mac
            self.start = timestamp
            self.duration = 0
            self.circuit_id = circuit_id
            self.remote_id = remote_id
            self.giaddr = giaddr
            self.new = False
        else:
            td = timestamp - self.start
            self.duration = (td.microseconds +
                             (td.seconds + td.days * 24 * 3600) *
                             10 ** 6) / 10 ** 6

        self.lease_time = lease_time

    def free(self, timestamp=None):
        if not self.new:
            if timestamp == None:
                self.end = self.start + timedelta(seconds=self.duration +
                                                  self.lease_time)
            else:
                self.end = timestamp

            td = self.end - self.start
            self.duration = (td.microseconds +
                             (td.seconds + td.days * 24 * 3600) *
                             10 ** 6) / 10 ** 6

            self.complete = True

    def add_sqlrow(self, sqlrow):
        self.rows.append(sqlrow)

    def reset(self):
        self.new = True
        self.complete = False
        self.rows = []
