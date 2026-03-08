-- Adminer 5.4.1 MySQL 8.0.45 dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

DROP TABLE IF EXISTS `ed_stay`;
CREATE TABLE `ed_stay` (
  `record_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `ed_timestamp` datetime NOT NULL,
  `activity` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`record_id`),
  KEY `stay_id_ed_timestamp_activity` (`stay_id`,`ed_timestamp`,`activity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `event_log`;
CREATE TABLE `event_log` (
  `event_log_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `time_to_triage` int DEFAULT NULL,
  `time_to_vital` int DEFAULT NULL,
  `time_to_medrecon` int DEFAULT NULL,
  `time_to_dispen` int DEFAULT NULL,
  `time_to_discharge` int DEFAULT NULL,
  `total_ed_stay_time` int DEFAULT NULL,
  `event_flow` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skipped_stages` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`event_log_id`),
  UNIQUE KEY `idx_unq_event_stay_id` (`stay_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `metrics`;
CREATE TABLE `metrics` (
  `metric_id` bigint NOT NULL AUTO_INCREMENT,
  `metric_name` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `avg_value` float NOT NULL,
  `p90_value` float NOT NULL,
  `p75_value` float NOT NULL,
  `p99_value` float NOT NULL,
  `min_value` float NOT NULL,
  `max_value` float NOT NULL,
  `stay_time_per_acuity` json NOT NULL,
  `upload_id` bigint NOT NULL,
  PRIMARY KEY (`metric_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `segment_summaries`;
CREATE TABLE `segment_summaries` (
  `upload_id` bigint NOT NULL,
  `segment_type` varchar(250) CHARACTER SET utf16 COLLATE utf16_unicode_ci NOT NULL,
  `segment_value` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `avg_stay_time` float NOT NULL,
  `p90_stay_time` float NOT NULL,
  `volume_count` int NOT NULL,
  KEY `upload_id` (`upload_id`),
  CONSTRAINT `segment_summaries_ibfk_1` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `stay_info`;
CREATE TABLE `stay_info` (
  `stay_info_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `gender` char(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `race` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `arrival_transport` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `disposition` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `chiefcomplaint` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `scale_level` smallint NOT NULL,
  PRIMARY KEY (`stay_info_id`),
  UNIQUE KEY `stay_id` (`stay_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `thresholds`;
CREATE TABLE `thresholds` (
  `threshold_id` int NOT NULL AUTO_INCREMENT,
  `threshold_name` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `threshold_value` int NOT NULL,
  PRIMARY KEY (`threshold_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `upload_history`;
CREATE TABLE `upload_history` (
  `upload_id` bigint NOT NULL AUTO_INCREMENT,
  `batch_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `upload_timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `period_start` datetime NOT NULL,
  `period_end` datetime NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  PRIMARY KEY (`upload_id`),
  UNIQUE KEY `batch_id` (`batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 2026-03-08 04:31:32 UTC
