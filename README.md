IPhistdb
========

IP history for ISC dhcpd 

Check INSTALL file for installation instructions.

This set of scripts parses dhcpd log files and imports history records 
into MySQL database.

Later lease history can be searched by using search.py script.

Multiple failover DHCP servers are supported as long as every server processes
log files to the same database. 
