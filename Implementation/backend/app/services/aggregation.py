from sqlalchemy import text
from app.core.database import engine

# calculate duration from Entry to each stage 
# insert into event_log table

cal_duration_event_log = """
INSERT INTO event_log (
    stay_id,
    entry_to_triage,
    entry_to_vital,
    entry_to_medrecon,
    entry_to_dispen,
    entry_to_discharge,
    skipped_stages
)
SELECT
    stay_id,
    -- calculate from Entry to each stage 
    -- to work in case of skipping termediate stages
    TIMESTAMPDIFF(MINUTE, t_entry, t_triage) as entry_to_triage,
    TIMESTAMPDIFF(MINUTE, t_entry, t_vital) as entry_to_vital,
    TIMESTAMPDIFF(MINUTE, t_entry, t_medrecon) as entry_to_medrecon,
    TIMESTAMPDIFF(MINUTE, t_entry, t_dispen) as entry_to_dispen,
    TIMESTAMPDIFF(MINUTE, t_entry, t_discharge) as entry_to_discharge,
    
    -- track to find which stages are skipped
    CONCAT(
        CASE WHEN t_triage IS NULL THEN 'Triage, ' ELSE '' END,
        CASE WHEN t_vital IS NULL THEN 'Vital, ' ELSE '' END,
        CASE WHEN t_medrecon IS NULL THEN 'Medrecon, ' ELSE '' END,
        CASE WHEN t_dispen IS NULL THEN 'Dispen, ' ELSE '' END
    ) AS skipped_stages
FROM (
    SELECT
        stay_id,
        MIN(CASE WHEN LOWER(TRIM(activity))='entry'     THEN ed_timestamp END) AS t_entry,
        MIN(CASE WHEN LOWER(TRIM(activity))='triage'    THEN ed_timestamp END) AS t_triage,
        MIN(CASE WHEN LOWER(TRIM(activity))='vital'     THEN ed_timestamp END) AS t_vital,
        MIN(CASE WHEN LOWER(TRIM(activity))='medrecon'  THEN ed_timestamp END) AS t_medrecon,
        MIN(CASE WHEN LOWER(TRIM(activity))='dispen'    THEN ed_timestamp END) AS t_dispen,
        MIN(CASE WHEN LOWER(TRIM(activity))='discharge' THEN ed_timestamp END) AS t_discharge
    FROM ed_stay
    GROUP BY stay_id
) x
WHERE t_entry IS NOT NULL
ON DUPLICATE KEY UPDATE
    entry_to_triage = VALUES(entry_to_triage),
    entry_to_vital = VALUES(entry_to_vital),
    entry_to_medrecon = VALUES(entry_to_medrecon),
    entry_to_dispen = VALUES(entry_to_dispen),
    entry_to_discharge = VALUES(entry_to_discharge),
    skipped_stages = VALUES(skipped_stages);
"""

def insert_duration_event() -> int:
    with engine.begin() as conn:
        result = conn.execute(text(cal_duration_event_log))
        return result.rowcount
    