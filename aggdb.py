# -*- coding: utf-8 -*-

"""aggdb related functions"""

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
import pytz


class AggDB:

    def __init__(self):
        self.lookup_tz = pytz.utc

    def connect(self, host, user, passwd, db):
        self._conn = MySQLdb.connect(host=host, user=user,
                                     passwd=passwd, db=db)

    def close(self):
        self._conn.close()

    def addlease(self, lease):
        """
        Adds aggregated lease to database.
        """
        c = self._conn.cursor()
        try:
            # Lease may already exist in table, for example
            # it can be incomplete lease. In this case
            # the end timestamp will be updated
            q = "INSERT INTO aggregated " \
                "(mac, ip, started, stopped, circuit_id, remote_id, giaddr) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s) " \
                "ON DUPLICATE KEY UPDATE "\
                "stopped=%s"
            c.execute(q, [lease.mac, lease.ip, lease.start, lease.end,
                          lease.circuit_id, lease.remote_id, lease.giaddr,
                          lease.end])

            self._conn.commit()

        finally:
            c.close()

    def cleanup(self, days=183):
        """
        Removes leases expired <days> ago
        """
        num_rows = 0
        c = self._conn.cursor()
        try:
            q = "DELETE from aggregated " \
                "WHERE stopped < NOW() - INTERVAL %s DAY"
            c.execute(q, [days])
            num_rows = c.rowcount
            self._conn.commit()

        finally:
            c.close()

        return num_rows

    def _generic_lookup(self, query, arguments, date_fmt):
        c = self._conn.cursor()
        try:
            c.arraysize = 16
            c.execute(query, arguments)

            while True:
                records = c.fetchmany()
                if len(records) == 0:
                    break

                for record in records:
                    result = {}
                    result["ip"] = record[0]
                    result["mac"] = record[1]
                    start = pytz.utc.localize(record[2]).astimezone(self.lookup_tz)
                    # converting to string because we need serializable type here
                    result["start"] = start.strftime(date_fmt)
                    end = pytz.utc.localize(record[3]).astimezone(self.lookup_tz)
                    result["end"] = end.strftime(date_fmt)
                    result["circuit_id"] = record[4]
                    result["remote_id"] = record[5]
                    result["giaddr"] = record[6]
                    result["tz"] = str(self.lookup_tz)

                    yield result

        finally:
            c.close()

    def lookup_by_ip(self, ip, date=None, date_fmt="%Y-%m-%d %H:%M:%S"):
        """
        Find leases by <ip>

        Arguments:
        ip -- IP address
        date -- naive date <ip> was leased
        """

        if date is None:
            q = "SELECT " \
                "ip, mac, started, stopped, circuit_id, remote_id, giaddr " \
                "FROM aggregated " \
                "WHERE ip=%s"
            a = [ip]
        else:
            utc_date = self.lookup_tz.localize(date).astimezone(pytz.utc)
            q = "SELECT " \
                "ip, mac, started, stopped, circuit_id, remote_id, giaddr " \
                "FROM aggregated " \
                "WHERE ip=%s AND started <= %s AND stopped >= %s"
            a = [ip, utc_date, utc_date]

        for result in self._generic_lookup(q, a, date_fmt):
            yield result

    def lookup_by_mac(self, mac, date=None, date_fmt="%Y-%m-%d %H:%M:%S"):
        """
        Find leases by <mac>

        Arguments:
        mac -- MAC address
        date -- naive date <mac> had a lease associated
        """
        if date is None:
            q = "SELECT " \
                "ip, mac, started, stopped, circuit_id, remote_id, giaddr " \
                "FROM aggregated " \
                "WHERE mac=%s"
            a = [mac]
        else:
            utc_date = self.lookup_tz.localize(date).astimezone(pytz.utc)
            q = "SELECT " \
                "ip, mac, started, stopped, circuit_id, remote_id, giaddr " \
                "FROM aggregated " \
                "WHERE mac=%s AND started <= %s AND stopped >= %s"
            a = [mac, utc_date, utc_date]

        for result in self._generic_lookup(q, a, date_fmt):
            yield result
