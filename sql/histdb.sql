CREATE TABLE `files` (
  `id_files` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `processed` datetime DEFAULT NULL,
  PRIMARY KEY (`id_files`),
  UNIQUE KEY `filename_UNIQUE` (`filename`),
  KEY `processed_IDX` (`processed`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

CREATE TABLE `history` (
  `id_history` int(11) NOT NULL AUTO_INCREMENT,
  `mac` varchar(12) DEFAULT NULL,
  `ip` varchar(15) NOT NULL,
  `timestamp` datetime NOT NULL,
  `lease_time` int(11) DEFAULT NULL,
  `circuit_id` varchar(255) DEFAULT NULL,
  `remote_id` varchar(255) DEFAULT NULL,
  `giaddr` varchar(15) DEFAULT NULL,
  `state` enum('LEASED','FREE') NOT NULL DEFAULT 'LEASED',
  PRIMARY KEY (`id_history`),
  UNIQUE KEY `iptimestampstate_UNIQUE` (`ip`,`timestamp`,`state`),
  KEY `ip_IDX` (`ip`),
  KEY `mac_IDX` (`mac`),
  KEY `state_IDX` (`state`),
  KEY `timestamp_IDX` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
