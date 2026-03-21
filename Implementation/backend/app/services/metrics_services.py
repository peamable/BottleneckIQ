from typing import Optional, List, Dict, Any
from sqlalchemy import text
import json
from app.core.database import engine

def get_latest_upload_id() -> Optional[int]:
    """Helper to find the most recent successful upload ID."""
    query = text("""
        SELECT upload_id FROM upload_history 
        WHERE status = 'completed' 
        ORDER BY upload_id DESC LIMIT 1
    """)
    with engine.connect() as conn:
        result = conn.execute(query).mappings().first()
        return result["upload_id"] if result else None
    
# For summary top-level metrics, we want to compare the current upload's metrics to the previous upload's metrics to calculate trends.
def calculate_trend(current: float, previous: float) -> Dict[str, Any]:
    """Calculates percentage change and ensures JSON-safe numbers."""
    # SQL AVG values may come back as Decimal depending on the driver.
    curr_val = float(current) if current is not None else 0.0
    prev_val = float(previous) if previous is not None else 0.0

    if prev_val == 0:
        return {"value": round(curr_val, 0), "trend": 0, "direction": "stable"}
    
    diff = curr_val - prev_val
    percent_change = round((abs(diff) / prev_val) * 100, 1)
    direction = "up" if diff > 0 else "down" if diff < 0 else "stable"
    
    return {"value": round(curr_val, 1), "trend": int(percent_change), "direction": direction}

def get_dashboard_summary(upload_id: int):
    metrics_sql = text("""
        SELECT 
            AVG(total_ed_stay_time) AS total_ed_stay_time,
            AVG(time_to_triage) AS time_to_triage,
            AVG(time_to_vital) AS time_to_vital,
            AVG(time_to_medrecon) AS time_to_medrecon,
            AVG(time_to_dispen) AS time_to_dispen,
            AVG(time_to_discharge) AS time_to_discharge
        FROM event_log
        WHERE upload_id = :u_id
    """)

    with engine.begin() as conn:
        curr = conn.execute(metrics_sql, {"u_id": upload_id}).mappings().first()

        prev_id = conn.execute(
            text("SELECT MAX(upload_id) FROM event_log WHERE upload_id < :u_id"),
            {"u_id": upload_id}
        ).scalar()

        prev = None
        if prev_id is not None:
            prev = conn.execute(metrics_sql, {"u_id": prev_id}).mappings().first()

    if not curr:
        return []

    def calculate_trend(current, previous):
        curr_val = float(current) if current is not None else 0.0
        prev_val = float(previous) if previous is not None else 0.0

        if prev_val == 0:
            return {
                "value": round(curr_val, 1),
                "trend": 0,
                "direction": "stable"
            }

        diff = curr_val - prev_val
        percent_change = round((abs(diff) / prev_val) * 100, 1)

        direction = "up" if diff > 0 else "down" if diff < 0 else "stable"

        return {
            "value": round(curr_val, 1),
            "trend": percent_change,
            "direction": direction
        }

    metric_keys = [
        "total_ed_stay_time",
        "time_to_triage",
        "time_to_vital",
        "time_to_medrecon",
        "time_to_dispen",
        "time_to_discharge",
    ]

    summary = []
    for key in metric_keys:
        trend_data = calculate_trend(curr[key], prev[key] if prev else 0)
        summary.append({
            "metric_name": key,
            "avg_value": trend_data["value"],
            "trend": trend_data["trend"],
            "direction": trend_data["direction"]
        })

    return summary

# Overall Avg Stay time per activity, and overall total stay time
# def get_metrics_data(upload_id: int, batch_id: Optional[str] = None) -> List[Dict[str, Any]]:
#     """Fetches and normalizes metrics for a specific ID."""
#     query_str = "SELECT * FROM metrics WHERE upload_id = :upload_id"
#     params = {"upload_id": upload_id}
    
#     if batch_id:
#         query_str += " AND batch_id = :batch_id"
#         params["batch_id"] = batch_id
        
#     query = text(query_str + " ORDER BY metric_name")
    
#     with engine.connect() as conn:
#         rows = conn.execute(query, params).mappings().all()

#     normalized_rows = []
#     for row in rows:
#         row_dict = dict(row)
#         # Handle the JSON string conversion safely
#         acuity_val = row_dict.get("stay_time_per_acuity")
#         if isinstance(acuity_val, str):
#             try:
#                 row_dict["stay_time_per_acuity"] = json.loads(acuity_val)
#             except json.JSONDecodeError:
#                 row_dict["stay_time_per_acuity"] = {}
#         normalized_rows.append(row_dict)
#     return normalized_rows


# Acuity Benchmarking Reference Data
ACUITY_REFERENCE = {
    1: {"name": "Level 1 (Resuscitation)", "ref_avg": 195, "color": "#2563eb"},
    2: {"name": "Level 2 (Emergent)", "ref_avg": 255, "color": "#ef4444"},
    3: {"name": "Level 3 (Urgent)", "ref_avg": 304, "color": "#f59e0b"},
    4: {"name": "Level 4 (Less Urgent)", "ref_avg": 193, "color": "#10b981"},
    5: {"name": "Level 5 (Non-Urgent)", "ref_avg": 98, "color": "#94a3b8"},
}

def get_avg_stay_time_by_acuity(upload_id: int) -> List[Dict[str, Any]]:
    query = text("""
        SELECT
            s.scale_level AS acuity_level,
            ROUND(AVG(t.total_ed_stay_time), 0) AS dept_avg
        FROM (
            SELECT
                e.stay_id,
                e.total_ed_stay_time
            FROM event_log e
            WHERE e.upload_id = :upload_id
            GROUP BY e.stay_id
        ) t
        JOIN stay_info s
            ON t.stay_id = s.stay_id
           AND s.upload_id = :upload_id
        WHERE s.scale_level IS NOT NULL
        GROUP BY s.scale_level
        ORDER BY s.scale_level
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    return [dict(row) for row in rows]

def build_acuity_benchmarks(upload_id: int) -> Dict[str, Any]:
    rows = get_avg_stay_time_by_acuity(upload_id)
    dept_map = {int(row["acuity_level"]): int(row["dept_avg"]) for row in rows}

    benchmarks = []
    for level, ref_data in ACUITY_REFERENCE.items():
        ref_avg = ref_data["ref_avg"]
        dept_avg = dept_map.get(level, 0)
        diff = dept_avg - ref_avg

        benchmarks.append({
            "name": ref_data["name"],
            "ref_esi_avg": f"{ref_avg}m",
            "dept_avg": f"{dept_avg}m",
            "diff": f"{diff:+}m",
            "type": "good" if diff <= 0 else "warning",
            "color": ref_data["color"]
        })

    return {"acuity_benchmarks": benchmarks}

def get_hourly_patient_density(upload_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves the 'Acuity Mix' per hour for the stacked bar chart.
    Each row represents one hour of the day (00:00 - 23:00).
    """
    query = text("""
        SELECT 
            hour_of_day, 
            SUM(acuity_1) as "Level 1",
            SUM(acuity_2) as "Level 2",
            SUM(acuity_3) as "Level 3",
            SUM(acuity_4) as "Level 4",
            SUM(acuity_5) as "Level 5"
        FROM temporal_summary
        WHERE upload_id = :u_id
        GROUP BY hour_of_day
        ORDER BY hour_of_day;
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(query, {"u_id": upload_id}).mappings().all()
        
        # We format the hour into "HH:00" strings so Recharts renders the X-axis nicely
        return [
            {
                "hour": f"{int(r['hour_of_day']):02d}:00",
                "Level 1": int(r["Level 1"]),
                "Level 2": int(r["Level 2"]),
                "Level 3": int(r["Level 3"]),
                "Level 4": int(r["Level 4"]),
                "Level 5": int(r["Level 5"])
            } 
            for r in rows
        ]
    

def get_performance_trend_data(lookback: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches historical metrics and labels them with the actual Upload Date and ID.
    Example Label: 'Oct 12 (ID: 42)'
    """
    
    # 1. Get the last N successful uploads with their real-world creation date
    history_query = text("""
        SELECT upload_id, upload_timestamp
        FROM upload_history
        WHERE status = 'completed'
        ORDER BY upload_id DESC
        LIMIT :limit
    """)

    # 2. Fetch the metrics for these specific uploads
    metrics_query = text("""
        SELECT 
            upload_id, 
            metric_name, 
            avg_value as p50, 
            p75_value as p75, 
            p90_value as p90
        FROM metrics
        WHERE upload_id IN :u_ids
    """)

    with engine.connect() as conn:
        history_rows = conn.execute(history_query, {"limit": lookback}).mappings().all()
        if not history_rows:
            return []

        u_ids = [r["upload_id"] for r in history_rows]
        metric_rows = conn.execute(metrics_query, {"u_ids": u_ids}).mappings().all()

    trend_data = []
    
    # Sort chronologically for the chart (Left = Oldest, Right = Newest)
    for upload in sorted(history_rows, key=lambda x: x["upload_id"]):
        u_id = upload["upload_id"]
        
        # Format the date nicely: e.g., "Oct 12"
        date_label = upload["upload_timestamp"].strftime("%b %d")
        
        entry = {
            "period_start": f"{date_label} (ID: {u_id})",
            "upload_id": u_id
        }

        # Filter and pivot metrics
        this_upload_metrics = [m for m in metric_rows if m["upload_id"] == u_id]
        for m in this_upload_metrics:
            name = m["metric_name"]
            entry[f"{name}_p50"] = m["p50"]
            entry[f"{name}_p75"] = m["p75"]
            entry[f"{name}_p90"] = m["p90"]

        trend_data.append(entry)

    return trend_data

def get_dashboard_horizon(upload_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Fetches the System Horizon (Upload Date and ID) for the dashboard header.
    Defaults to the most recent upload if no ID is provided.
    """
    
    # If no ID, find the latest one first
    if upload_id is None:
        upload_id = get_latest_upload_id()

    if not upload_id:
        return {"upload_id": None, "display_date": "No Data Available"}

    # Grab the timestamp for this specific upload
    query = text("""
        SELECT upload_timestamp 
        FROM upload_history 
        WHERE upload_id = :u_id
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"u_id": upload_id}).mappings().one_or_none()

    if result and result["upload_timestamp"]:
        # Format: "Feb 22, 2026 | 14:30"
        formatted_date = result["upload_timestamp"].strftime("%b %d, %Y | %H:%M")
        return {
            "upload_id": upload_id,
            "display_date": formatted_date
        }

    return {"upload_id": upload_id, "display_date": "Unknown Date"}
