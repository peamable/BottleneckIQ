import pandas as pd
from sqlalchemy import text
from app.core.database import engine

# calculate duration from Entry to each stage 
# insert into event_log table

<<<<<<< Updated upstream
cal_duration_event_log = """
INSERT INTO event_log (
    stay_id,
    time_to_triage,
    time_to_vital,
    time_to_medrecon,
    time_to_dispen,
    time_to_discharge,
    total_ed_stay,
    skipped_stages
)
SELECT
    stay_id,
    -- calculate from Entry to each stage 
    -- to work in case of skipping termediate stages
    TIMESTAMPDIFF(MINUTE, t_entry, t_triage) as time_to_triage,
    TIMESTAMPDIFF(MINUTE, t_triage, t_vital) as time_to_vital,
    TIMESTAMPDIFF(MINUTE, t_vital, t_medrecon) as time_to_medrecon,
    TIMESTAMPDIFF(MINUTE, t_medrecon, t_dispen) as time_to_dispen,
    TIMESTAMPDIFF(MINUTE, t_dispen, t_discharge) as time_to_discharge,
    TIMESTAMPDIFF(MINUTE, t_entry, t_discharge) as total_ed_stay,
    
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
    time_to_triage = VALUES(time_to_triage),
    time_to_vital = VALUES(time_to_vital),
    time_to_medrecon = VALUES(time_to_medrecon),
    time_to_dispen = VALUES(time_to_dispen),
    time_to_discharge = VALUES(time_to_discharge),
    total_ed_stay = VALUES(total_ed_stay),
    skipped_stages = VALUES(skipped_stages);
"""

=======
>>>>>>> Stashed changes
def insert_duration_event() -> int:
    # Fetch all data sorted by stay_id and timestamp
    query = "SELECT stay_id, activity, ed_timestamp FROM ed_stay ORDER BY stay_id, ed_timestamp"
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        return 0
    
    # Mapping dictionary for the numeric flow
    FLOW_MAP = {
        'entry': 1, 'triage': 2, 'vital': 3, 
        'medrecon': 4, 'dispen': 5, 'discharge': 6
    }

    results = []

    # Group by stay_id to process each patient's journey
    for stay_id, group in df.groupby('stay_id'):
        # group is already sorted by ed_timestamp because of our SQL ORDER BY
        # Sort group by timestamp to ensure flow and durations are chronological
        group = group.sort_values('ed_timestamp')

        rows = group.to_dict('records')

        # Calculate Total Length of Stay (Last timestamp - First timestamp)
        total_los = (rows[-1]['ed_timestamp'] - rows[0]['ed_timestamp']).total_seconds() / 60.0
        
        # Build the Numeric Flow string (e.g., "1 -> 2 -> 4 -> 6")
        # We use .get(..., 0) to handle any unexpected activity names safely
        flow_steps = [str(FLOW_MAP.get(r['activity'].lower().strip(), 0)) for r in rows]
        event_flow = " -> ".join(flow_steps)

        # We will still store results in your existing table structure
        metrics = {
            'stay_id': stay_id,
            'event_flow': event_flow,
            'total_ed_stay': total_los, #total length of stay
            'time_to_triage': None, 'time_to_vital': None,
            'time_to_medrecon': None, 'time_to_dispen': None,
            'time_to_discharge': None, 'skipped_stages': []
        }

        # NEW LOGIC: Step through the events one by one
        for i in range(1, len(rows)):
            prev_event = rows[i-1]
            curr_event = rows[i]
            
            # Calculate duration of THIS segment
            delta_min = (curr_event['ed_timestamp'] - prev_event['ed_timestamp']).total_seconds() / 60.0
            
            # MAP TO YOUR COLUMNS: 
            # If the 'current' event is Triage, we now know exactly how long they 
            # waited since the previous event (whatever that was!)
            stage_key = f"time_to_{curr_event['activity'].lower()}"
            if stage_key in metrics:
                metrics[stage_key] = delta_min

        # Detect skipped stages by checking what is still None
        expected_stages = ['triage', 'vital', 'medrecon', 'dispen']
        for s in expected_stages:
            if metrics[f'time_to_{s}'] is None:
                metrics['skipped_stages'].append(s.capitalize())
                
        metrics['skipped_stages'] = ", ".join(metrics['skipped_stages'])
        results.append(metrics)
        
    if not results:
        return 0

    upsert_sql = text("""
        INSERT INTO event_log (
            stay_id, time_to_triage, time_to_vital, time_to_medrecon, 
            time_to_dispen, time_to_discharge, skipped_stages, event_flow, total_ed_stay
        ) VALUES (
            :stay_id, :time_to_triage, :time_to_vital, :time_to_medrecon, 
            :time_to_dispen, :time_to_discharge, :skipped_stages, :event_flow, :total_ed_stay
        )
        ON DUPLICATE KEY UPDATE
            time_to_triage = VALUES(time_to_triage),
            time_to_vital = VALUES(time_to_vital),
            time_to_medrecon = VALUES(time_to_medrecon),
            time_to_dispen = VALUES(time_to_dispen),
            time_to_discharge = VALUES(time_to_discharge),
            skipped_stages = VALUES(skipped_stages),
            event_flow = VALUES(event_flow),
            total_ed_stay = VALUES(total_ed_stay)
    """)

    with engine.begin() as conn:
        conn.execute(upsert_sql, results)
        
    return len(results)
    