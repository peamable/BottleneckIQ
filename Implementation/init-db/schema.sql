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
  `total_ed_stay` int DEFAULT NULL,
  `event_flow` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skipped_stages` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`event_log_id`),
  UNIQUE KEY `idx_unq_event_stay_id` (`stay_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `metrics`;
CREATE TABLE `metrics` (
  `metric_id` bigint NOT NULL AUTO_INCREMENT,
  `metric_name` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `avg_value` int NOT NULL,
  `p90_value` int NOT NULL,
  `num_patient_hrly` int NOT NULL,
  `stay_time_per_acuity` int NOT NULL,
  `period_start` timestamp NOT NULL,
  `period_end` timestamp NOT NULL,
  PRIMARY KEY (`metric_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `stay_info`;
CREATE TABLE `stay_info` (
  `stay_info_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `gender` char(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `race` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `arrival_transport` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `scale_level` smallint NOT NULL,
  `chiefcomplaint` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
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


-- 2026-03-04 04:43:11 UTC
