#!/usr/bin/python
# -*- coding: utf-8 -*-

"""histdb maintenance procedures"""

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


# Add this file to cron.daily or cron.d (see INSTALL)

from ConfigParser import ConfigParser
from iphistdb.histdb import HistDB


config_filename = "/etc/IPhistdb/config.ini"


def main():
    db = HistDB()
    cfg = ConfigParser()

    cfg.read(config_filename)

    db.connect(cfg.get("MySQL", "host"),
               cfg.get("MySQL", "user"),
               cfg.get("MySQL", "pass"),
               cfg.get("MySQL", "db"))

    db.cleanup(cfg.get("Maintenance", "forget_files_after"))


if __name__ == "__main__":
    main()
