-- Adminer 5.4.1 MySQL 8.0.45 dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

DROP TABLE IF EXISTS `acuity`;
CREATE TABLE `acuity` (
  `acuity_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `scale_level` smallint NOT NULL,
  PRIMARY KEY (`acuity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `ed_stay`;
CREATE TABLE `ed_stay` (
  `record_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `timestamp` timestamp NOT NULL,
  `activity` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`record_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `event_log`;
CREATE TABLE `event_log` (
  `event_log_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `entry_to_triage` int NOT NULL,
  `triage_to_vital` int NOT NULL,
  `vital_to_medrecon` int NOT NULL,
  `medrecon_to_dispen` int NOT NULL,
  `dispen_to_discharge` int NOT NULL,
  PRIMARY KEY (`event_log_id`)
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


DROP TABLE IF EXISTS `thresholds`;
CREATE TABLE `thresholds` (
  `threshold_id` int NOT NULL AUTO_INCREMENT,
  `threshold_name` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `threshold_value` int NOT NULL,
  PRIMARY KEY (`threshold_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- 2026-02-04 03:59:07 UTC
