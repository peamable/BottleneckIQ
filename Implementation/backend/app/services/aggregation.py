import pandas as pd
from sqlalchemy import text
from app.core.database import engine

def insert_duration_event(upload_id: int | None = None) -> int:
    query = text("""
        SELECT stay_id, activity, ed_timestamp, upload_id
        FROM ed_stay
        WHERE (:upload_id IS NULL OR upload_id = :upload_id)
        ORDER BY stay_id, ed_timestamp
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"upload_id": upload_id})

    # De-duplicate the data to handle cases where the same file is uploaded twice.
    # This ensures each event in a patient's journey is considered only once.
    df = df.drop_duplicates()

    if df.empty:
        return 0

    FLOW_MAP = {
        'entry': 1, 'triage': 2, 'vital': 3,
        'medrecon': 4, 'dispen': 5, 'discharge': 6
    }

    results = []

    for stay_id, group in df.groupby('stay_id'):
        group = group.sort_values('ed_timestamp')
        rows = group.to_dict('records')

        total_los = (rows[-1]['ed_timestamp'] - rows[0]['ed_timestamp']).total_seconds() / 60.0
        current_upload_id = rows[0]["upload_id"]

        flow_steps = [str(FLOW_MAP.get(r['activity'].lower().strip(), 0)) for r in rows]
        event_flow = " -> ".join(flow_steps)

        metrics = {
            'stay_id': stay_id,
            'upload_id': current_upload_id,
            'event_flow': event_flow,
            'total_ed_stay_time': total_los,
            'time_to_triage': None,
            'time_to_vital': None,
            'time_to_medrecon': None,
            'time_to_dispen': None,
            'time_to_discharge': None,
            'skipped_stages': []
        }

        for i in range(1, len(rows)):
            prev_event = rows[i - 1]
            curr_event = rows[i]

            delta_min = (curr_event['ed_timestamp'] - prev_event['ed_timestamp']).total_seconds() / 60.0

            stage_key = f"time_to_{curr_event['activity'].lower()}"
            if stage_key in metrics:
                metrics[stage_key] = delta_min

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
            stay_id, upload_id, time_to_triage, time_to_vital, time_to_medrecon,
            time_to_dispen, time_to_discharge, skipped_stages, event_flow, total_ed_stay_time
        ) VALUES (
            :stay_id, :upload_id, :time_to_triage, :time_to_vital, :time_to_medrecon,
            :time_to_dispen, :time_to_discharge, :skipped_stages, :event_flow, :total_ed_stay_time
        )
        ON DUPLICATE KEY UPDATE
            time_to_triage = VALUES(time_to_triage),
            time_to_vital = VALUES(time_to_vital),
            time_to_medrecon = VALUES(time_to_medrecon),
            time_to_dispen = VALUES(time_to_dispen),
            time_to_discharge = VALUES(time_to_discharge),
            skipped_stages = VALUES(skipped_stages),
            event_flow = VALUES(event_flow),
            total_ed_stay_time = VALUES(total_ed_stay_time),
            upload_id = VALUES(upload_id)
    """)

    with engine.begin() as conn:
        conn.execute(upsert_sql, results)

    return len(results)
