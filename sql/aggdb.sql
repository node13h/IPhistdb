CREATE TABLE `aggregated` (
  `id_aggregated` int(11) NOT NULL auto_increment,
  `mac` varchar(12) NOT NULL,
  `ip` varchar(15) NOT NULL,
  `started` datetime NOT NULL,
  `stopped` datetime NOT NULL,
  `circuit_id` varchar(255) default NULL,
  `remote_id` varchar(255) default NULL,
  `giaddr` varchar(15) default NULL,
  PRIMARY KEY  (`id_aggregated`),
  UNIQUE KEY `ip_started_UNIQUE` (`ip`,`started`),
  KEY `ip_IDX` (`ip`),
  KEY `mac_IDX` (`mac`),
  KEY `ip_started_stopped_IDX` (`ip`,`started`,`stopped`),
  KEY `mac_started_stopped_IDX` (`mac`,`started`,`stopped`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

