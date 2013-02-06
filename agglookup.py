#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Simple program to lookup records in aggregated IP history database"""

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

import sys
from ConfigParser import ConfigParser
from aggdb import AggDB
from datetime import datetime

config_filename = "/etc/IPhistdb/aggregate.ini"
fmt = "{0:<16} {1:<13} {2:<20} {3:<20} {4:<30} {5:<20} {6:>16}"


def main(argv):
    db = AggDB()
    cfg = ConfigParser()

    cfg.read(config_filename)

    db.connect(cfg.get("MySQL", "host"),
               cfg.get("MySQL", "user"),
               cfg.get("MySQL", "pass"),
               cfg.get("MySQL", "db"))

    target_date = datetime.strptime(argv[1], "%Y-%m-%d %H:%M:%S")

    print fmt.format("IP", "MAC", "Start", "End", "Circuit-ID",
                     "Remote-ID", "giaddr")

    for item in db.lookup_by_ip(argv[0], target_date, target_date):

        print fmt.format(item["ip"], item["mac"],
                         item["start"].strftime("%Y-%m-%d %H:%M:%S"),
                         item["end"].strftime("%Y-%m-%d %H:%M:%S"),
                         item["circuit_id"],
                         item["remote_id"],
                         item["giaddr"])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: " + sys.argv[0] + " <IP> <YYYY-MM-DD hh:mm:ss>"
    else:
        main(sys.argv[1:])
