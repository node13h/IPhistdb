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


class AggDB:

    def connect(self, host, user, passwd, db):
        self._conn = MySQLdb.connect(host=host, user=user,
                                     passwd=passwd, db=db)

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

    # TODO
    def lookup_by_ip(self, ip, earliest, latest):
        """
        Find leases by <ip>

        Arguments:
        ip -- IP address
        earliest -- earliest date <ip> was leased
        latest -- latest date <ip> was leased
        """
        pass

    def lookup_by_mac(self, mac, earliest, latest):
        """
        Find leases by <mac>

        Arguments:
        mac -- MAC address
        earliest -- earliest date <mac> had a lease associated
        latest -- latest date <mac> had a lease associated
        """
        pass
