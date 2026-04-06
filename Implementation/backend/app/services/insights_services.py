import os
import sys
import re
import math
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy import text

if __name__ == "__main__":
    # Allow direct execution via `python app/services/insights_services.py`.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

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


def get_temporal_heatmap(upload_id: Optional[int] = None, lookback: int = 3) -> dict:
    """Builds a 7x4 daily heatmap (4x6h slices) for patient volume using temporal_summary from recent uploads."""
    effective_id = upload_id or get_latest_upload_id()
    day_labels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    slice_labels = ['Dawn ', 'Morning ', 'Afternoon ', 'Night ']

    if not effective_id:
        return {
            "upload_id": None,
            "day_labels": day_labels,
            "slice_labels": slice_labels,
            "volume_matrix": [[0,0,0,0] for _ in range(7)]
        }

    # Get the last N completed upload IDs to aggregate recent patterns
    recent_uploads_query = text("""
        SELECT upload_id
        FROM upload_history
        WHERE status = 'completed'
        ORDER BY upload_id DESC
        LIMIT :lookback
    """)

    with engine.connect() as conn:
        recent_rows = conn.execute(recent_uploads_query, {"lookback": lookback}).mappings().all()
        recent_upload_ids = [row['upload_id'] for row in recent_rows]

    if not recent_upload_ids:
        return {
            "upload_id": effective_id,
            "day_labels": day_labels,
            "slice_labels": slice_labels,
            "volume_matrix": [[0,0,0,0] for _ in range(7)]
        }

    query = text("""
        SELECT
            ((day_of_week - 1) % 7) AS dow,
            FLOOR(hour_of_day / 6) AS slice,
            AVG(total_volume) AS avg_volume
        FROM temporal_summary
        WHERE upload_id IN :u_ids
        GROUP BY dow, slice
        ORDER BY dow, slice;
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"u_ids": tuple(recent_upload_ids)}).mappings().all()

    volume_matrix = [[0, 0, 0, 0] for _ in range(7)]

    for row in rows:
        dow = int(row['dow']) if row['dow'] is not None else 0
        slice_idx = int(row['slice']) if row['slice'] is not None else 0
        if 0 <= dow <= 6 and 0 <= slice_idx <= 3:
            volume_matrix[dow][slice_idx] = round(float(row['avg_volume'] or 0))

    return {
        "upload_id": effective_id,
        "day_labels": day_labels,
        "slice_labels": slice_labels,
        "volume_matrix": volume_matrix
    }


def get_stage_temporal_forecast(upload_id: Optional[int] = None, lookback: int = 3) -> dict:
    """Stage-specific hourly bottleneck risk with now/next-hour recommendations."""
    effective_id = upload_id or get_latest_upload_id()
    day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    stages = ["vital", "medrecon", "dispen", "discharge"]

    empty_hourly = [
        {
            "hour_of_day": h,
            "time_label": f"{h:02d}:00",
            "vital": 0.0,
            "medrecon": 0.0,
            "dispen": 0.0,
            "discharge": 0.0,
            "sample_size": 0,
        }
        for h in range(24)
    ]

    now_dt = datetime.now()
    next_dt = now_dt + timedelta(hours=1)
    tomorrow_dt = now_dt + timedelta(days=1)

    if not effective_id:
        return {
            "upload_id": None,
            "evaluated_upload_ids": [],
            "generated_at": now_dt.isoformat(timespec="seconds"),
            "day_labels": day_labels,
            "today_hourly_risk": empty_hourly,
            "weekday_risk": [],
            "current_context": {
                "day_of_week": now_dt.weekday(),
                "day_label": day_labels[now_dt.weekday()],
                "hour_of_day": now_dt.hour,
                "next_hour_day_of_week": next_dt.weekday(),
                "next_hour_day_label": day_labels[next_dt.weekday()],
                "next_day_of_week": next_dt.weekday(),
                "next_day_label": day_labels[tomorrow_dt.weekday()],
                "next_hour_of_day": next_dt.hour,
            },
            "current_slot": None,
            "next_slot": None,
            "current_day_summary": None,
            "next_day_summary": None,
            "alerts": [],
        }

    recent_uploads_query = text("""
        SELECT upload_id
        FROM upload_history
        WHERE status = 'completed'
        ORDER BY upload_id DESC
        LIMIT :lookback
    """)

    with engine.connect() as conn:
        recent_rows = conn.execute(recent_uploads_query, {"lookback": lookback}).mappings().all()
        recent_upload_ids = [row["upload_id"] for row in recent_rows]

    if not recent_upload_ids:
        recent_upload_ids = [effective_id]

    base_query = text("""
        WITH first_event AS (
            SELECT
                upload_id,
                stay_id,
                MIN(ed_timestamp) AS first_ts
            FROM ed_stay
            WHERE upload_id IN :u_ids
            GROUP BY upload_id, stay_id
        )
        SELECT
            fe.first_ts,
            el.time_to_vital,
            el.time_to_medrecon,
            el.time_to_dispen,
            el.time_to_discharge
        FROM first_event fe
        JOIN event_log el
          ON el.upload_id = fe.upload_id
         AND el.stay_id = fe.stay_id
    """)

    with engine.connect() as conn:
        df = pd.read_sql(base_query, conn, params={"u_ids": tuple(recent_upload_ids)})

    if df.empty:
        return {
            "upload_id": effective_id,
            "evaluated_upload_ids": recent_upload_ids,
            "generated_at": now_dt.isoformat(timespec="seconds"),
            "day_labels": day_labels,
            "today_hourly_risk": empty_hourly,
            "weekday_risk": [],
            "current_context": {
                "day_of_week": now_dt.weekday(),
                "day_label": day_labels[now_dt.weekday()],
                "hour_of_day": now_dt.hour,
                "next_hour_day_of_week": next_dt.weekday(),
                "next_hour_day_label": day_labels[next_dt.weekday()],
                "next_day_of_week": next_dt.weekday(),
                "next_day_label": day_labels[tomorrow_dt.weekday()],
                "next_hour_of_day": next_dt.hour,
            },
            "current_slot": None,
            "next_slot": None,
            "current_day_summary": None,
            "next_day_summary": None,
            "alerts": [],
        }

    df["first_ts"] = pd.to_datetime(df["first_ts"], errors="coerce")
    df = df.dropna(subset=["first_ts"]).copy()
    df["day_of_week"] = df["first_ts"].dt.dayofweek
    df["hour_of_day"] = df["first_ts"].dt.hour

    thresholds = {}
    for stage in stages:
        col = f"time_to_{stage}"
        series = pd.to_numeric(df[col], errors="coerce")
        thresholds[stage] = float(series.dropna().quantile(0.90)) if series.notna().any() else None
        flag_col = f"is_bottleneck_{stage}"
        if thresholds[stage] is None:
            df[flag_col] = 0
        else:
            df[flag_col] = ((series > thresholds[stage]) & series.notna()).astype(int)

    grouped = (
        df.groupby(["day_of_week", "hour_of_day"], as_index=False)
        .agg(
            sample_size=("first_ts", "size"),
            vital=("is_bottleneck_vital", "mean"),
            medrecon=("is_bottleneck_medrecon", "mean"),
            dispen=("is_bottleneck_dispen", "mean"),
            discharge=("is_bottleneck_discharge", "mean"),
        )
    )

    for stage in stages:
        grouped[stage] = (grouped[stage] * 100.0).round(1)

    weekday_grouped = (
        df.groupby(["day_of_week"], as_index=False)
        .agg(
            sample_size=("first_ts", "size"),
            vital=("is_bottleneck_vital", "mean"),
            medrecon=("is_bottleneck_medrecon", "mean"),
            dispen=("is_bottleneck_dispen", "mean"),
            discharge=("is_bottleneck_discharge", "mean"),
        )
    )
    for stage in stages:
        weekday_grouped[stage] = (weekday_grouped[stage] * 100.0).round(1)

    weekday_map = {
        int(row["day_of_week"]): {
            "day_of_week": int(row["day_of_week"]),
            "day_label": day_labels[int(row["day_of_week"])],
            "vital": float(row["vital"]),
            "medrecon": float(row["medrecon"]),
            "dispen": float(row["dispen"]),
            "discharge": float(row["discharge"]),
            "sample_size": int(row["sample_size"]),
        }
        for _, row in weekday_grouped.iterrows()
    }
    weekday_risk = [
        weekday_map.get(
            d,
            {
                "day_of_week": d,
                "day_label": day_labels[d],
                "vital": 0.0,
                "medrecon": 0.0,
                "dispen": 0.0,
                "discharge": 0.0,
                "sample_size": 0,
            },
        )
        for d in range(7)
    ]

    today_idx = now_dt.weekday()
    today_rows = grouped[grouped["day_of_week"] == today_idx].copy()

    today_map = {
        int(row["hour_of_day"]): {
            "hour_of_day": int(row["hour_of_day"]),
            "time_label": f"{int(row['hour_of_day']):02d}:00",
            "vital": float(row["vital"]),
            "medrecon": float(row["medrecon"]),
            "dispen": float(row["dispen"]),
            "discharge": float(row["discharge"]),
            "sample_size": int(row["sample_size"]),
        }
        for _, row in today_rows.iterrows()
    }
    today_hourly_risk = [today_map.get(h, empty_hourly[h]) for h in range(24)]

    def get_slot(day_idx: int, hour_idx: int):
        slot = grouped[(grouped["day_of_week"] == day_idx) & (grouped["hour_of_day"] == hour_idx)]
        if slot.empty:
            return None
        row = slot.iloc[0]
        return {
            "day_of_week": day_idx,
            "day_label": day_labels[day_idx],
            "hour_of_day": hour_idx,
            "time_label": f"{hour_idx:02d}:00",
            "vital": float(row["vital"]),
            "medrecon": float(row["medrecon"]),
            "dispen": float(row["dispen"]),
            "discharge": float(row["discharge"]),
            "sample_size": int(row["sample_size"]),
        }

    current_slot = get_slot(now_dt.weekday(), now_dt.hour)
    next_slot = get_slot(next_dt.weekday(), next_dt.hour)

    valid_weekday_rows = [r for r in weekday_risk if int(r.get("sample_size", 0)) > 0]
    if valid_weekday_rows:
        weighted_fallback = {
            "day_of_week": -1,
            "day_label": "Historical Average",
            "sample_size": int(sum(r["sample_size"] for r in valid_weekday_rows)),
            "vital": round(sum(r["vital"] * r["sample_size"] for r in valid_weekday_rows) / sum(r["sample_size"] for r in valid_weekday_rows), 1),
            "medrecon": round(sum(r["medrecon"] * r["sample_size"] for r in valid_weekday_rows) / sum(r["sample_size"] for r in valid_weekday_rows), 1),
            "dispen": round(sum(r["dispen"] * r["sample_size"] for r in valid_weekday_rows) / sum(r["sample_size"] for r in valid_weekday_rows), 1),
            "discharge": round(sum(r["discharge"] * r["sample_size"] for r in valid_weekday_rows) / sum(r["sample_size"] for r in valid_weekday_rows), 1),
        }
    else:
        weighted_fallback = {
            "day_of_week": -1,
            "day_label": "Historical Average",
            "sample_size": 0,
            "vital": 0.0,
            "medrecon": 0.0,
            "dispen": 0.0,
            "discharge": 0.0,
        }

    current_day_summary = weekday_map.get(now_dt.weekday(), weighted_fallback)
    next_day_summary = weekday_map.get(tomorrow_dt.weekday(), weighted_fallback)

    alerts = []
    if next_slot is not None:
        for stage in stages:
            next_risk = float(next_slot[stage])
            now_risk = float(current_slot[stage]) if current_slot is not None else 0.0
            if next_risk >= 30.0 or next_risk >= now_risk + 5.0:
                stage_name = {
                    "vital": "Vitals",
                    "medrecon": "Medication Reconciliation",
                    "dispen": "Medication Dispensing",
                    "discharge": "Discharge",
                }[stage]
                alerts.append(
                    {
                        "stage": stage,
                        "stage_label": stage_name,
                        "risk_now": round(now_risk, 1),
                        "risk_next": round(next_risk, 1),
                        "message": f"{stage_name} bottleneck risk rises next hour ({round(now_risk,1)}% -> {round(next_risk,1)}%).",
                        "recommendation": f"Prepare {stage_name.lower()} capacity before {next_dt.hour:02d}:00.",
                    }
                )

    return {
        "upload_id": effective_id,
        "evaluated_upload_ids": recent_upload_ids,
        "generated_at": now_dt.isoformat(timespec="seconds"),
        "day_labels": day_labels,
        "today_hourly_risk": today_hourly_risk,
        "weekday_risk": weekday_risk,
        "current_context": {
            "day_of_week": now_dt.weekday(),
            "day_label": day_labels[now_dt.weekday()],
            "hour_of_day": now_dt.hour,
            "next_hour_day_of_week": next_dt.weekday(),
            "next_hour_day_label": day_labels[next_dt.weekday()],
            "next_day_of_week": tomorrow_dt.weekday(),
            "next_day_label": day_labels[tomorrow_dt.weekday()],
            "next_hour_of_day": next_dt.hour,
        },
        "current_slot": current_slot,
        "next_slot": next_slot,
        "current_day_summary": current_day_summary,
        "next_day_summary": next_day_summary,
        "alerts": alerts,
    }


def get_event_flow_forecast_insights(upload_id: Optional[int] = None, lookback: int = 3) -> dict:
    """Summarize high-risk event flow pathways for operational forecasting."""
    effective_id = upload_id or get_latest_upload_id()
    if not effective_id:
        return {
            "upload_id": None,
            "evaluated_upload_ids": [],
            "top_delay_flows": [],
            "summary": "No data available",
        }

    recent_uploads_query = text("""
        SELECT upload_id
        FROM upload_history
        WHERE status = 'completed'
        ORDER BY upload_id DESC
        LIMIT :lookback
    """)
    with engine.connect() as conn:
        recent_rows = conn.execute(recent_uploads_query, {"lookback": lookback}).mappings().all()
        recent_upload_ids = [row["upload_id"] for row in recent_rows]

    if not recent_upload_ids:
        recent_upload_ids = [effective_id]

    total_query = text("""
        SELECT COUNT(*) AS cnt
        FROM event_log
        WHERE upload_id IN :u_ids
          AND event_flow IS NOT NULL
          AND event_flow <> ''
    """)

    flows_query = text("""
        SELECT
            event_flow,
            COUNT(*) AS stay_count,
            AVG(total_ed_stay_time) AS avg_los_min,
            SUM(CASE WHEN skipped_stages IS NOT NULL AND skipped_stages <> '' THEN 1 ELSE 0 END) AS skipped_count
        FROM event_log
        WHERE upload_id IN :u_ids
          AND event_flow IS NOT NULL
          AND event_flow <> ''
          AND total_ed_stay_time IS NOT NULL
        GROUP BY event_flow
        HAVING COUNT(*) >= 5
        ORDER BY avg_los_min DESC
        LIMIT 8
    """)

    flow_step_map = {
        "1": "entry",
        "2": "triage",
        "3": "vital",
        "4": "medrecon",
        "5": "dispen",
        "6": "discharge",
    }

    def decode_flow(raw: str) -> str:
        parts = [p.strip() for p in str(raw).split("->")]
        labels = [flow_step_map.get(p, p) for p in parts if p]
        return " -> ".join(labels)

    with engine.connect() as conn:
        total_row = conn.execute(total_query, {"u_ids": tuple(recent_upload_ids)}).mappings().first()
        flow_rows = conn.execute(flows_query, {"u_ids": tuple(recent_upload_ids)}).mappings().all()

    total_count = int(total_row["cnt"]) if total_row and total_row["cnt"] is not None else 0
    if total_count == 0:
        return {
            "upload_id": effective_id,
            "evaluated_upload_ids": recent_upload_ids,
            "top_delay_flows": [],
            "summary": "No event flow records available",
        }

    top_delay_flows = []
    for row in flow_rows:
        stay_count = int(row["stay_count"] or 0)
        avg_los_min = float(row["avg_los_min"] or 0)
        skipped_count = int(row["skipped_count"] or 0)
        skipped_pct = round((skipped_count / stay_count) * 100, 1) if stay_count else 0.0
        share_pct = round((stay_count / total_count) * 100, 1)
        share_label = "<0.1%" if stay_count > 0 and share_pct == 0.0 else f"{share_pct}%"

        top_delay_flows.append(
            {
                "event_flow": str(row["event_flow"]),
                "event_flow_label": decode_flow(str(row["event_flow"])),
                "avg_los_min": round(avg_los_min, 1),
                "stay_count": stay_count,
                "share_pct": share_pct,
                "share_label": share_label,
                "skipped_stage_pct": skipped_pct,
                "recommendation": (
                    "Standardize handoff checkpoints for this pathway"
                    if skipped_pct >= 25.0
                    else "Pre-stage staff/resources for this pathway during peaks"
                ),
            }
        )

    return {
        "upload_id": effective_id,
        "evaluated_upload_ids": recent_upload_ids,
        "top_delay_flows": top_delay_flows,
        "summary": "Pathways ranked by highest average ED LOS",
    }


# disposition mix pie chart visualization
def get_disposition_mix(upload_id: int) -> dict:
    # We query the permanent table 'stay_info'
    # Since we aren't using upload_id yet, we get the distribution of all processed records
    query = text("""
        SELECT
            CASE
                WHEN LOWER(TRIM(disposition)) = 'home' THEN 'Home'
                WHEN LOWER(TRIM(disposition)) = 'admitted' THEN 'Admitted'
                WHEN LOWER(TRIM(disposition)) IN (
                    'eloped',
                    'left without being seen',
                    'left against medical advice',
                    'expired',
                    'transfer',
                    'other'
                ) THEN 'Other'
                ELSE 'Other'
            END AS disposition_group,
            COUNT(DISTINCT stay_id) AS cnt,
            ROUND(
                COUNT(DISTINCT stay_id) * 100.0
                / SUM(COUNT(DISTINCT stay_id)) OVER (),
                2
            ) AS pct
        FROM stay_info
        WHERE disposition IS NOT NULL
        AND disposition <> ''
        AND upload_id = :upload_id
        GROUP BY disposition_group
        ORDER BY pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    disposition_mix = [
        {
            "type": r["disposition_group"],
            "count": int(r["cnt"]),
            "percentage": float(round(r["pct"], 2))
        }
        for r in rows
    ]

    return disposition_mix

# chiefcomplaint top 5 bar chart visualization
def get_top_chief_complaints(upload_id: int) -> dict:
    query = text("""
        WITH stay_duration AS (
            SELECT
                stay_id,
                upload_id,
                MAX(total_ed_stay_time) AS total_ed_stay_time
            FROM event_log
            WHERE total_ed_stay_time IS NOT NULL
              AND upload_id = :upload_id
            GROUP BY stay_id, upload_id
        )
        SELECT
            si.chiefcomplaint,
            COUNT(*) AS cnt,
            AVG(sd.total_ed_stay_time) AS avg_total_ed_stay_time
        FROM stay_info si
        JOIN stay_duration sd
            ON si.stay_id = sd.stay_id
           AND si.upload_id = sd.upload_id
        WHERE si.upload_id = :upload_id
          AND si.chiefcomplaint IS NOT NULL
          AND si.chiefcomplaint <> ''
        GROUP BY si.chiefcomplaint
        ORDER BY cnt DESC
        LIMIT 5
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    top_chief_complaints = [
        {
            "chiefcomplaint": r["chiefcomplaint"],
            "count": r["cnt"],
            "avg_total_ed_stay_time": float(round(r["avg_total_ed_stay_time"], 2)) if r["avg_total_ed_stay_time"] is not None else None
        }
        for r in rows
    ]

    return top_chief_complaints

# chief complaint count bar chart visualization
def get_chief_complaint_counts(upload_id: int) -> list[dict]:
    query = text("""
        SELECT
            chiefcomplaint,
            COUNT(*) AS count
        FROM stay_info
        WHERE upload_id = :upload_id
          AND chiefcomplaint IS NOT NULL
          AND chiefcomplaint <> ''
        GROUP BY chiefcomplaint
        ORDER BY count DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    chief_complaint_counts = [
        {
            "chiefcomplaint": r["chiefcomplaint"],
            "count": r["count"]
        }
        for r in rows
    ]

    return chief_complaint_counts

# Demographics flow audit bar chart visualization

def get_equity_audit(upload_id: int) -> list[dict]:
    query = text("""
        WITH stay_duration AS (
            SELECT
                stay_id,
                upload_id,
                MAX(total_ed_stay_time) AS total_ed_stay_time
            FROM event_log
            WHERE total_ed_stay_time IS NOT NULL
              AND upload_id = :upload_id
            GROUP BY stay_id, upload_id
        ),
        base AS (
            SELECT
                si.race,
                sd.total_ed_stay_time
            FROM stay_info si
            JOIN stay_duration sd
              ON si.stay_id = sd.stay_id
             AND si.upload_id = sd.upload_id
            WHERE si.upload_id = :upload_id
              AND si.race IS NOT NULL
              AND si.race <> ''
        ),
        overall AS (
            SELECT
                AVG(total_ed_stay_time) AS overall_avg_stay_time
            FROM base
        )
        SELECT
            b.race,
            COUNT(*) AS cnt,
            ROUND(AVG(b.total_ed_stay_time), 2) AS race_avg_stay_time,
            ROUND(o.overall_avg_stay_time, 2) AS overall_avg_stay_time,
            ROUND(
                ((AVG(b.total_ed_stay_time) - o.overall_avg_stay_time) / o.overall_avg_stay_time) * 100,
                2
            ) AS variance_pct
        FROM base b
        CROSS JOIN overall o
        GROUP BY b.race, o.overall_avg_stay_time
        ORDER BY variance_pct DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"upload_id": upload_id}).mappings().all()

    equity_audit = [
         {
            "group": r["race"],
            "variance": float(r["variance_pct"]),
            #"race_avg_total_ed_stay_time": float(r["race_avg_stay_time"]),
            #"overall_avg_total_ed_stay_time": float(r["overall_avg_stay_time"]),
            #"count": int(r["cnt"])
        }
        for r in rows
    ]

    return equity_audit

def get_bed_occupancy_analysis_by_case_mix(upload_id: int):
    query = text("""
        SELECT
            e.stay_id,
            COALESCE(NULLIF(TRIM(s.chiefcomplaint), ''), 'unknown / missing') AS chiefcomplaint,
            MAX(e.total_ed_stay_time) / 60 AS los_hours
        FROM event_log e
        LEFT JOIN stay_info s
            ON s.stay_id = e.stay_id
           AND s.upload_id = e.upload_id
        WHERE e.upload_id = :u_id
          AND e.total_ed_stay_time IS NOT NULL
        GROUP BY e.stay_id, COALESCE(NULLIF(TRIM(s.chiefcomplaint), ''), 'unknown / missing')
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"u_id": upload_id})

    if df.empty:
        return []

    draft_operational_keywords = {
        "Gen_Health_Symptoms": [
            "tachycardia", "hypotension", "palpitations", "allergic reaction",
            "ear pain", "rash",
            "dental pain", "tooth pain", 
            "weakness", "htn", "weight loss dehydration",
            "cellulitis", "abscess", "wound infection", "skin infection",
            "dysuria", "uti", "urinary frequency", "hematuria",
            "anorexia", "epistaxis", "r eye pain visual changes",
            "body aches", "lightheaded",  "allergic rxn",
            "visual changes", "hypoxia", "epigatric pain ercp",
            "dizzy nausea", "weak", "hemoptysis", "hypertension", 
    
        ],
        "Fever": [
            "influenza like illness", "ili", "viral syndrome", "flu like illness", 
            "sore throat", "fever", "febrile", "chills",  "fever", "cough","fevers",
            "throat foreign body sensation", "pneumonia transfer", "sepsis",
        ],
        "Injury": [
            "mvc", "motor vehicle crash", "motor vehicle collision",
            "status post fall", "fall", "injury", "wound eval",  "laceration",
            "motorcycle accident", "status post assault", "head bleed", "headbleed",
            "ankle inj", "gsw", "abrasion", "assault", "bicycle accident",
            "facial laceration", "burn", "wound check",
        ],
        "chest_pain/Sob": [ 
            "chest pain", "dyspnea", "shortness of breath" , "sob", 
            "respiratory distress", "respiratory failure", "asthma exacerbation",
            "chest pains", "stemi",
        ],
        "Abdominal/Pelvic_Pain": [
            "abdominal pain", "flank pain", "quadrant abdominal pain",
            "lower abdominal pain", "right lower quadrant",
            "left lower quadrant", "right upper quadrant",
            "upper quadrant abdominal", "inguinal pain",
            "acute pelvic pain", "pelvic pain", "groin pain",
            "rectal pain", "epigastric pain", "v d n",
        ],
        "Back/Extremity_Pain": [
            "back pain", "lower back pain", "neck pain", "shoulder pain",
            "leg pain", "arm pain", "hip pain", "knee pain",
            "ankle pain", "finger pain", "hand pain", "wrist pain",
            "foot pain", "toe pain", "l sided rib pain", "r sided rib pain",
            "lower extremity pain", "upper extremity pain",
        ],
        "Neuro": [
            "headache", "syncope", "seizure", "stroke",
            "dizziness", "numbness", "migraine", "dizzziness", "sah", "sah transfer", 
            "facial droop", "slurred speech", "agitation", "basic trauma", 
            "vertigo", "double vision", "seizures",
        ],
        "Psychiatric": [
            "altered mental status", "mental status",
            "psych", "si", "behavioral", "depression", "clearance", 
            "anxiety", "hallucination", "paranoid", "hallucinations", 
            "requests eval bizarre behaviour", "panic attack", "hearing voices",
            "confusion", "psychiatric hold", 

        ],   
        "GI_Symptoms": [
            "bright red blood per rectum", "brbpr", "gi bleed",
            "rectal bleed", "bloody stool", "melena", 
            "sbo", "n v", "n v d", "constipation", "nausea vomitting",
            "abdominal distention", "diarrhea", "vomiting",
            "difficulty swallowing", "hematemesis", 
        ],
        "Alcohol/Sub_Use": [
            "alcohol intoxication", "etoh intoxication", "drug intoxication",
            "substance misuse intoxication","heroin od", "substance use",
            "drug overdose", "overdose", "etoh withdrawal", "alcohol withdrawal",
        ],
       
        "Eval/FU/Abn_Tests": [
            "for eval", "re eval", "recheck", "follow up","refill", "abnormal labs",
            "abnormal mri", "abnormal ct", "abnormal xray", "abnormal ultrasound",
            "suture removal", "needs ct scan", "gtube eval", "blocked ngt",
            "ng tube eval", "medical device problem", "hyperglycemia",
            "abnormal lab values",
        ],
    }

    compiled_patterns = {
        group: re.compile(
            r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b"
        )
        for group, keywords in draft_operational_keywords.items()
    }

    def normalize_complaint(text):
        if pd.isna(text):
            return "unknown / missing"

        text = str(text).lower().strip()
        if not text:
            return "unknown / missing"

        replacements = {
            r"\bh/a\b": "headache",
            r"\bsob\b": "shortness of breath",
            r"\betoh\b": "alcohol intoxication",
            r"\bams\b": "altered mental status",
            r"\babd\b": "abdominal",
            r"\bs/p\b": "status post",
            r"\bcva\b": "stroke",
            r"\bili\b": "influenza like illness",
            r"\bbrbpr\b": "bright red blood per rectum",
            r"\blac\b": "laceration",
        }
        for pat, repl in replacements.items():
            text = re.sub(pat, repl, text)

        text = re.sub(r"[/,;:+()\-]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def map_to_op_group(text):
        text = normalize_complaint(text)
        if text == "unknown / missing":
            return "Unknown/Missing"
        for group, pattern in compiled_patterns.items():
            if pattern.search(text):
                return group
        return "Other/Misc"

    def has_transfer_flag(text):
        text = normalize_complaint(text)
        return int(bool(re.search(r"\btransfer\b", text)))

    df["chiefcomplaint_clean"] = df["chiefcomplaint"].apply(normalize_complaint)
    df["op_group"] = df["chiefcomplaint"].apply(map_to_op_group)
    df["is_transfer"] = df["chiefcomplaint"].apply(has_transfer_flag)

    other_misc_counts = (
    df.loc[df["op_group"] == "Other/Misc", "chiefcomplaint_clean"]
    .value_counts()
    .sort_values(ascending=False)
)
    if not other_misc_counts.empty:
        print(f"Reached bottleneck function for upload_id={upload_id}", flush=True)
        print(other_misc_counts.to_string(), flush=True)



    stats = (
        df.groupby("op_group")
        .agg(
            patient_count=("op_group", "count"),
            avg_los=("los_hours", "mean"),
            total_bed_hours=("los_hours", "sum"),
            transfer_count=("is_transfer", "sum"),
        )
        .reset_index()
        .sort_values(by="total_bed_hours", ascending=False)
    )

    stats["transfer_pct"] = (
        stats["transfer_count"] / stats["patient_count"] * 100
    ).round(2)

#    print(f"\n--- OPERATIONAL BOTTLENECKS (ID: {upload_id}) ---")
#    print(stats[[
#        "op_group", "patient_count", "transfer_count",
#        "transfer_pct", "total_bed_hours"
#    ]].head(10))

    return [
        {
            "label": row["op_group"],
            "value": round(row["total_bed_hours"], 2),
            "avg_los": round(row["avg_los"], 2),
            "count": int(row["patient_count"]),
            "transfer_count": int(row["transfer_count"]),
            "transfer_pct": float(row["transfer_pct"]),
        }
        for _, row in stats.iterrows()
    ]

# P90 total ED stay time vs patient volume correlation scatter plot visualization
def get_p90_total_ed_stay_time_volume_correlations():
    sql = text("""
        SELECT
            u.upload_id,
            m.p90_value,
            COUNT(DISTINCT s.stay_id) AS patient_volume
        FROM upload_history u
        JOIN metrics m
            ON u.upload_id = m.upload_id
        AND m.metric_name = 'total_ed_stay_time'
        LEFT JOIN stay_info s
            ON u.upload_id = s.upload_id
        GROUP BY u.upload_id, m.p90_value
        ORDER BY u.upload_id;
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()

    return {
        "p90_total_ed_stay_time_volume_correlations": [
            {
                "upload_id": row["upload_id"],
                "patient_volume": int(row["patient_volume"]),
                "p90_total_ed_stay_time": float(row["p90_value"])
            }
            for row in rows
        ]
    }
# disposition breakdown by milestone bar chart visualization
def get_disposition_milestone_breakdown(upload_id: int):
    query = text("""
        SELECT 
            si.disposition,
            AVG(e.time_to_vital) AS avg_vital,
            AVG(e.time_to_medrecon) AS avg_medrecon,
            AVG(e.time_to_dispen) AS avg_dispen,
            AVG(e.time_to_discharge) AS avg_discharge
        FROM event_log e
        JOIN stay_info si
          ON e.stay_id = si.stay_id
         AND e.upload_id = si.upload_id
        WHERE e.upload_id = :u_id
          AND si.disposition IN ('Admitted', 'Home')
        GROUP BY si.disposition
    """)

    with engine.begin() as conn:
        rows = conn.execute(query, {"u_id": upload_id}).mappings().all()

    def safe_float(value):
        if value is None:
            return None
        value = float(value)
        return None if math.isnan(value) else value

    result = {
        "upload_id": upload_id,
        "disposition_milestone_analysis": {
            "admitted": {
                "avg_vital": None,
                "avg_medrecon": None,
                "avg_dispen": None,
                "avg_discharge": None
            },
            "home": {
                "avg_vital": None,
                "avg_medrecon": None,
                "avg_dispen": None,
                "avg_discharge": None
            }
        }
    }

    for row in rows:
        disposition = str(row["disposition"]).strip().lower()
        if disposition in result["disposition_milestone_analysis"]:
            result["disposition_milestone_analysis"][disposition] = {
                "avg_vital": safe_float(row["avg_vital"]),
                "avg_medrecon": safe_float(row["avg_medrecon"]),
                "avg_dispen": safe_float(row["avg_dispen"]),
                "avg_discharge": safe_float(row["avg_discharge"])
            }

    return result

# acuity level milestone bar chart visualization
def get_acuity_level_breakdown(upload_id: int):
    query = text("""
        SELECT 
            si.scale_level,
            AVG(e.time_to_triage) AS avg_triage,
            AVG(e.time_to_vital) AS avg_vital,
            AVG(e.time_to_medrecon) AS avg_medrecon,
            AVG(e.time_to_dispen) AS avg_dispen,
            AVG(e.time_to_discharge) AS avg_discharge,
            AVG(e.total_ed_stay_time) AS avg_total_stay
        FROM event_log e
        JOIN stay_info si
          ON e.stay_id = si.stay_id
         AND e.upload_id = si.upload_id
        WHERE e.upload_id = :u_id
          AND si.scale_level IS NOT NULL
        GROUP BY si.scale_level
        ORDER BY si.scale_level
    """)

    with engine.begin() as conn:
        rows = conn.execute(query, {"u_id": upload_id}).mappings().all()

    def safe_float(value):
        if value is None:
            return None
        value = float(value)
        return None if math.isnan(value) else value

    return {
        "upload_id": upload_id,
        "acuity_level_analysis": [
            {
                "scale_level": int(row["scale_level"]),
                "avg_triage": safe_float(row["avg_triage"]),
                "avg_vital": safe_float(row["avg_vital"]),
                "avg_medrecon": safe_float(row["avg_medrecon"]),
                "avg_dispen": safe_float(row["avg_dispen"]),
                "avg_discharge": safe_float(row["avg_discharge"]),
                "avg_total_stay": safe_float(row["avg_total_stay"]),
            }
            for row in rows
            if row["scale_level"] is not None
        ]
    }
