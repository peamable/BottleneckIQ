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
  `upload_id` bigint NOT NULL,
  PRIMARY KEY (`record_id`),
  UNIQUE KEY `idx_unq_ed_stay_upload_event` (`stay_id`,`ed_timestamp`,`activity`,`upload_id`),
  KEY `upload_id` (`upload_id`),
  CONSTRAINT `ed_stay_ibfk_3` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `ed_stay_staging`;
CREATE TABLE `ed_stay_staging` (
  `stay_id` bigint DEFAULT NULL,
  `ed_timestamp` datetime DEFAULT NULL,
  `activity` varchar(255) DEFAULT NULL,
  `batch_id` varchar(50) DEFAULT NULL,
  `upload_id` bigint DEFAULT NULL,
  `ingested_at` datetime DEFAULT NULL,
  KEY `idx_upload_id` (`upload_id`),
  CONSTRAINT `fk_ed_stay_upload` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


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
  `upload_id` bigint DEFAULT NULL,
  PRIMARY KEY (`event_log_id`),
  UNIQUE KEY `idx_unq_event_stay_upload` (`stay_id`,`upload_id`),
  KEY `upload_id` (`upload_id`),
  CONSTRAINT `event_log_ibfk_1` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `hourly_aggregates`;
CREATE TABLE `hourly_aggregates` (
  `timestamp_hour` datetime DEFAULT NULL,
  `total_volume` bigint DEFAULT NULL,
  `acuity_1` bigint DEFAULT NULL,
  `acuity_2` bigint DEFAULT NULL,
  `acuity_3` bigint DEFAULT NULL,
  `acuity_4` bigint DEFAULT NULL,
  `acuity_5` bigint DEFAULT NULL,
  `month_of_year` int DEFAULT NULL,
  `day_of_week` int DEFAULT NULL,
  `hour_of_day` int DEFAULT NULL,
  `upload_id` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


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
  PRIMARY KEY (`metric_id`),
  UNIQUE KEY `idx_unq_metrics_upload_metric` (`upload_id`,`metric_name`),
  KEY `upload_id` (`upload_id`),
  CONSTRAINT `metrics_ibfk_1` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `bottleneck_status_counts`;
CREATE TABLE `bottleneck_status_counts` (
  `bottleneck_status_count_id` bigint NOT NULL AUTO_INCREMENT,
  `upload_id` bigint NOT NULL,
  `stage` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `patient_count` int NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`bottleneck_status_count_id`),
  UNIQUE KEY `idx_unq_bottleneck_upload_stage_status` (`upload_id`,`stage`,`status`),
  KEY `idx_bottleneck_status_upload` (`upload_id`),
  CONSTRAINT `bottleneck_status_counts_ibfk_1` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE
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
  `gender` char(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `race` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `arrival_transport` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `disposition` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `chiefcomplaint` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `scale_level` smallint DEFAULT NULL,
  `upload_id` bigint NOT NULL,
  PRIMARY KEY (`stay_info_id`),
  UNIQUE KEY `idx_unq_stay_info_upload` (`stay_id`,`upload_id`),
  KEY `upload_id` (`upload_id`),
  CONSTRAINT `stay_info_ibfk_1` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `stay_info_staging`;
CREATE TABLE `stay_info_staging` (
  `stay_id` bigint DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `race` varchar(255) DEFAULT NULL,
  `arrival_transport` varchar(255) DEFAULT NULL,
  `disposition` varchar(255) DEFAULT NULL,
  `scale_level` double DEFAULT NULL,
  `chiefcomplaint` varchar(255) DEFAULT NULL,
  `batch_id` varchar(50) DEFAULT NULL,
  `upload_id` bigint DEFAULT NULL,
  `ingested_at` datetime DEFAULT NULL,
  KEY `idx_upload_id` (`upload_id`),
  CONSTRAINT `fk_stay_info_upload` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `temporal_summary`;
CREATE TABLE `temporal_summary` (
  `aggregate_id` bigint NOT NULL AUTO_INCREMENT,
  `timestamp_hour` datetime NOT NULL,
  `total_volume` int NOT NULL,
  `month_of_year` int NOT NULL,
  `day_of_week` int NOT NULL,
  `hour_of_day` int NOT NULL,
  `acuity_1` int DEFAULT '0',
  `acuity_2` int DEFAULT '0',
  `acuity_3` int DEFAULT '0',
  `acuity_4` int DEFAULT '0',
  `acuity_5` int DEFAULT '0',
  `upload_id` bigint NOT NULL,
  PRIMARY KEY (`aggregate_id`),
  UNIQUE KEY `idx_unq_temporal_summary_upload_hour` (`upload_id`,`timestamp_hour`),
  KEY `upload_id` (`upload_id`),
  CONSTRAINT `temporal_summary_ibfk_1` FOREIGN KEY (`upload_id`) REFERENCES `upload_history` (`upload_id`)
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
  `batch_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `upload_timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `period_start` datetime NOT NULL,
  `period_end` datetime NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  PRIMARY KEY (`upload_id`),
  UNIQUE KEY `batch_id` (`batch_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 2026-03-15 21:50:10 UTC
