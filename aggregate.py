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
from iphistdb.histdb import HistDB
from iphistdb.aggdb import AggDB
import logging
import logging.config

hconfig_filename = "/etc/IPhistdb/config.ini"
aconfig_filename = "/etc/IPhistdb/aggregate.ini"
config_logging_filename = "/etc/IPhistdb/aggregate.logging.ini"


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

    logging.config.fileConfig(config_logging_filename)
    logger = logging.getLogger("file")

    # All history:
    for item in hdb.aggregate_history():
        adb.addlease(item)
        if item.complete:
            hdb.del_history_records(item.rows)
            logger.debug(str(item.rows) + " IDs deleted from history")

    nr = adb.cleanup(cfg.get("Maintenance", "record_keep_days"))
    logger.info(str(nr) + " leases deleted from aggregated")


if __name__ == "__main__":
    main(sys.argv[1:])
