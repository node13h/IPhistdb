IPhistdb
========

IP history for ISC dhcpd 

Check INSTALL file for installation instructions.

DHCP servers log lease events in logfile. Data from these logs collected
by IPhistdb/process.py and imported into SQL database (history table).
Each lease may have multiple records, because DHCP client re-leases
IP address periodically (every 1/2 of the lease-time typically).

The IPhistdb/aggregate.py is also run daily, to aggregate lease data from
history table into aggregated table. There is no way to safely aggregate data
straight from the log file into aggregated table, because DHCP leases can
last years, and log files may be rotated during that time leading to loss
of information about lease start. Also there can be more than one DHCP
server(clustering), so different parts of the same lease may end up recorded
in logfiles of different servers.

Later aggregated DB data can be used directly or via IPhistdb-API app
(see https://github.com/node13h/IPhistdb-API)

Multiple failover DHCP servers are supported as long as every server processes
log files to the same database. 
