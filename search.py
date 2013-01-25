#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Simple program to search IP history database"""

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
from histdb import HistDB
from datetime import datetime

config_filename = "/etc/IPhistdb/config.ini"
fmt = "{0:<16} {1:<13} {2:<20} {3:<20} {4:<30} {5:<20} {6:>16}"


def main(argv):
    db = HistDB()
    cfg = ConfigParser()

    cfg.read(config_filename)

    db.connect(cfg.get("MySQL", "host"),
               cfg.get("MySQL", "user"),
               cfg.get("MySQL", "pass"),
               cfg.get("MySQL", "db"))

    if len(argv) == 2:
        target_date = datetime.strptime(argv[1], "%Y-%m-%d %H:%M:%S")
    else:
        target_date = None

    print fmt.format("IP", "MAC", "Start", "End", "Circuit-ID",
                     "Remote-ID", "giaddr")

    for item in db.aggregate_history(argv[0]):

        if target_date == None or item.start <= target_date <= item.end:

            print fmt.format(item.ip, item.mac,
                             item.start.strftime("%Y-%m-%d %H:%M:%S"),
                             item.end.strftime("%Y-%m-%d %H:%M:%S"),
                             item.circuit_id,
                             item.remote_id,
                             item.giaddr)


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print "Usage: " + sys.argv[0] + " <IP> [<YYYY-MM-DD hh:mm:ss>]"
    else:
        main(sys.argv[1:])
