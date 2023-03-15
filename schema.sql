-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               10.6.12-MariaDB-1:10.6.12+maria~deb11 - mariadb.org binary distribution
-- Server OS:                    debian-linux-gnu
-- HeidiSQL Version:             12.4.0.6659
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Dumping structure for table odbs.drives
CREATE TABLE IF NOT EXISTS `drives` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `task` int(10) unsigned NOT NULL,
  `group` varchar(1) NOT NULL,
  `size` bigint(20) DEFAULT NULL,
  `free_space` bigint(20) DEFAULT NULL,
  `ts_registered` bigint(20) NOT NULL,
  `ts_lastindex` bigint(20) DEFAULT NULL,
  `ts_lastsync` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ts_registered` (`ts_registered`),
  KEY `ts_lastindex` (`ts_lastindex`),
  KEY `ts_lastsync` (`ts_lastsync`),
  KEY `task` (`task`),
  KEY `size` (`size`),
  KEY `group` (`group`),
  KEY `freesize` (`free_space`),
  CONSTRAINT `link_drives_tasks` FOREIGN KEY (`task`) REFERENCES `tasks` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Data exporting was unselected.

-- Dumping structure for table odbs.files
CREATE TABLE IF NOT EXISTS `files` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `task` int(10) unsigned NOT NULL,
  `extension` varchar(255) NOT NULL,
  `source_volume` varchar(50) NOT NULL,
  `source_path` text NOT NULL,
  `source_last_seen` bigint(20) NOT NULL,
  `source_size` bigint(20) NOT NULL,
  `source_checksum` varchar(255) NOT NULL,
  `source_missing` int(1) NOT NULL DEFAULT 0,
  `backup_a_drive` int(10) unsigned DEFAULT NULL,
  `backup_a_path` text DEFAULT NULL,
  `backup_a_date` bigint(20) unsigned DEFAULT NULL,
  `backup_b_drive` int(10) unsigned DEFAULT NULL,
  `backup_b_path` text DEFAULT NULL,
  `backup_b_date` bigint(20) unsigned DEFAULT NULL,
  `backup_c_drive` int(10) unsigned DEFAULT NULL,
  `backup_c_path` text DEFAULT NULL,
  `backup_c_date` bigint(20) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `filename` (`filename`),
  KEY `source_volume` (`source_volume`),
  KEY `source_last_seen` (`source_last_seen`),
  KEY `source_size` (`source_size`),
  KEY `source_checksum` (`source_checksum`),
  KEY `backup_task` (`task`) USING BTREE,
  KEY `extension` (`extension`) USING BTREE,
  KEY `source_missing` (`source_missing`),
  KEY `backup_a_drive` (`backup_a_drive`),
  KEY `backup_a_date` (`backup_a_date`),
  KEY `backup_b_drive` (`backup_b_drive`),
  KEY `backup_b_date` (`backup_b_date`),
  KEY `backup_c_drive` (`backup_c_drive`),
  KEY `backup_c_date` (`backup_c_date`),
  CONSTRAINT `link_files_tasks` FOREIGN KEY (`task`) REFERENCES `tasks` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=571045 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Data exporting was unselected.

-- Dumping structure for table odbs.tasks
CREATE TABLE IF NOT EXISTS `tasks` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `path` varchar(255) NOT NULL,
  `desc` text DEFAULT NULL,
  `ts_creation` bigint(20) unsigned NOT NULL,
  `ts_lastedit` bigint(20) unsigned NOT NULL,
  `ts_lastindex` bigint(20) unsigned NOT NULL DEFAULT 0,
  `ts_lastexec` bigint(20) unsigned NOT NULL DEFAULT 0,
  `status_lastexec` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `path` (`path`),
  KEY `ts_creation` (`ts_creation`),
  KEY `ts_lastindex` (`ts_lastindex`),
  KEY `ts_lastbackup` (`ts_lastexec`) USING BTREE,
  KEY `last_status` (`status_lastexec`),
  KEY `ls_lastedit` (`ts_lastedit`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Data exporting was unselected.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
