#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Transfers aggregated ip history to SQL table. Run it
daily as a cron job
"""

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
from aggdb import AggDB
import logging

hconfig_filename = "/etc/IPhistdb/config.ini"
aconfig_filename = "/etc/IPhistdb/aggregate.ini"


def main(argv):
    hdb = HistDB()
    adb = AggDB()
    cfg = ConfigParser()

    cfg.read(hconfig_filename)

    hdb.connect(cfg.get("MySQL", "host"),
                cfg.get("MySQL", "user"),
                cfg.get("MySQL", "pass"),
                cfg.get("MySQL", "db"))

    cfg.read(aconfig_filename)
    adb.connect(cfg.get("MySQL", "host"),
                cfg.get("MySQL", "user"),
                cfg.get("MySQL", "pass"),
                cfg.get("MySQL", "db"))

    logger = logging.getLogger("aggregate")

    loglevels = {"NOTSET": logging.NOTSET, "DEBUG": logging.DEBUG,
                 "INFO": logging.INFO, "WARNING": logging.WARNING,
                 "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}

    logger.setLevel(loglevels[cfg.get("Logging", "level")])

    fh = logging.FileHandler(filename=cfg.get("Logging", "logfile"))

    lformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    fh.setFormatter(logging.Formatter(lformat))

    logger.addHandler(fh)

    # All history:
    for item in hdb.aggregate_history():
        adb.addlease(item)
        hdb.del_history_records(item.rows)
        logger.debug(str(item.rows) + " IDs deleted from history")

    nr = adb.cleanup(cfg.get("Maintenance", "record_keep_days"))
    logger.debug(str(nr) + "leases deleted from aggregated")


if __name__ == "__main__":
    main(sys.argv[1:])
