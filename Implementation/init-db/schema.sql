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
  PRIMARY KEY (`acuity_id`),
  UNIQUE KEY `stay_id` (`stay_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `acuity_staging`;
CREATE TABLE `acuity_staging` (
  `stay_id` bigint DEFAULT NULL,
  `scale_level` double DEFAULT NULL,
  `batch_id` varchar(50) DEFAULT NULL,
  `ingested_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `ed_stay`;
CREATE TABLE `ed_stay` (
  `record_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `ed_timestamp` datetime NOT NULL,
  `activity` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`record_id`),
  KEY `stay_id_ed_timestamp_activity` (`stay_id`,`ed_timestamp`,`activity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `ed_stay_staging`;
CREATE TABLE `ed_stay_staging` (
  `stay_id` bigint DEFAULT NULL,
  `ed_timestamp` datetime DEFAULT NULL,
  `activity` varchar(255) DEFAULT NULL,
  `batch_id` varchar(50) DEFAULT NULL,
  `ingested_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `event_log`;
CREATE TABLE `event_log` (
  `event_log_id` bigint NOT NULL AUTO_INCREMENT,
  `stay_id` bigint NOT NULL,
  `entry_to_triage` int DEFAULT NULL,
  `entry_to_vital` int DEFAULT NULL,
  `entry_to_medrecon` int DEFAULT NULL,
  `entry_to_dispen` int DEFAULT NULL,
  `entry_to_discharge` int DEFAULT NULL,
  `skipped_stages` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
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


DROP TABLE IF EXISTS `thresholds`;
CREATE TABLE `thresholds` (
  `threshold_id` int NOT NULL AUTO_INCREMENT,
  `threshold_name` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `threshold_value` int NOT NULL,
  PRIMARY KEY (`threshold_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP VIEW IF EXISTS `v_step_differences`;
CREATE TABLE `v_step_differences` (`stay_id` bigint, `gap_entry_triage` int, `gap_triage_vital` bigint, `gap_vital_medrecon` bigint, `gap_medrecon_dispen` bigint, `gap_dispen_discharge` bigint, `total_duration` int, `workflow_status` varchar(14));


DROP TABLE IF EXISTS `v_step_differences`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `v_step_differences` AS select `event_log`.`stay_id` AS `stay_id`,`event_log`.`entry_to_triage` AS `gap_entry_triage`,(`event_log`.`entry_to_vital` - `event_log`.`entry_to_triage`) AS `gap_triage_vital`,(`event_log`.`entry_to_medrecon` - `event_log`.`entry_to_vital`) AS `gap_vital_medrecon`,(`event_log`.`entry_to_dispen` - `event_log`.`entry_to_medrecon`) AS `gap_medrecon_dispen`,(`event_log`.`entry_to_discharge` - `event_log`.`entry_to_dispen`) AS `gap_dispen_discharge`,`event_log`.`entry_to_discharge` AS `total_duration`,(case when (((`event_log`.`entry_to_vital` - `event_log`.`entry_to_triage`) < 0) or ((`event_log`.`entry_to_medrecon` - `event_log`.`entry_to_vital`) < 0) or ((`event_log`.`entry_to_dispen` - `event_log`.`entry_to_medrecon`) < 0) or ((`event_log`.`entry_to_discharge` - `event_log`.`entry_to_dispen`) < 0)) then 'Out of Order' when ((`event_log`.`entry_to_triage` is null) or (`event_log`.`entry_to_vital` is null) or (`event_log`.`entry_to_discharge` is null)) then 'Skipped Stages' else 'Normal' end) AS `workflow_status` from `event_log`;

-- 2026-02-18 03:22:48 UTC
