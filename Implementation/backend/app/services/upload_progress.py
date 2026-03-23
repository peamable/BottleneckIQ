from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.core.database import engine


STAGE_DEFS = [
    ("file_saved", "File Saved"),
    ("cleaning", "Cleaning"),
    ("staging", "Staging"),
    ("validation", "Validation"),
    ("ingestion", "Ingestion"),
    ("aggregation", "Aggregation"),
    ("analytics", "Analytics"),
]


CREATE_UPLOAD_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS upload_progress (
  upload_id BIGINT PRIMARY KEY,
  batch_id VARCHAR(100) NOT NULL,
  payload_json LONGTEXT NOT NULL,
  updated_at DATETIME NOT NULL,
  CONSTRAINT fk_upload_progress_history
    FOREIGN KEY (upload_id) REFERENCES upload_history(upload_id) ON DELETE CASCADE
);
"""


def _ensure_upload_progress_table() -> None:
    with engine.begin() as conn:
        conn.execute(text(CREATE_UPLOAD_PROGRESS_TABLE))


def _default_stages() -> list[dict[str, str]]:
    return [{"key": key, "label": label, "status": "pending"} for key, label in STAGE_DEFS]


def _load_job(upload_id: int) -> dict[str, Any] | None:
    _ensure_upload_progress_table()
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT payload_json
            FROM upload_progress
            WHERE upload_id = :upload_id
        """), {"upload_id": upload_id}).mappings().first()

    if not row:
        return None
    return json.loads(row["payload_json"])


def _save_job(upload_id: int, batch_id: str, payload: dict[str, Any]) -> None:
    _ensure_upload_progress_table()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO upload_progress (upload_id, batch_id, payload_json, updated_at)
            VALUES (:upload_id, :batch_id, :payload_json, :updated_at)
            ON DUPLICATE KEY UPDATE
              batch_id = VALUES(batch_id),
              payload_json = VALUES(payload_json),
              updated_at = VALUES(updated_at)
        """), {
            "upload_id": upload_id,
            "batch_id": batch_id,
            "payload_json": json.dumps(payload),
            "updated_at": datetime.now(),
        })


def init_upload_job(upload_id: int, batch_id: str, file_path: str) -> None:
    payload = {
        "upload_id": upload_id,
        "batch_id": batch_id,
        "file_path": file_path,
        "status": "processing",
        "message": "Upload queued.",
        "allow_skip": False,
        "missing_fields": [],
        "validation_issues": [],
        "skipped_rows": [],
        "processed_with_skips": False,
        "stages": _default_stages(),
    }
    _save_job(upload_id, batch_id, payload)


def update_stage(upload_id: int, stage_key: str, status: str, message: str | None = None) -> None:
    job = _load_job(upload_id)
    if not job:
        return

    for stage in job["stages"]:
        if stage["key"] == stage_key:
            stage["status"] = status
            break

    if message is not None:
        job["message"] = message

    _save_job(upload_id, job["batch_id"], job)


def set_job_state(upload_id: int, **updates: Any) -> None:
    job = _load_job(upload_id)
    if not job:
        return

    job.update(updates)
    _save_job(upload_id, job["batch_id"], job)


def get_upload_job(upload_id: int) -> dict[str, Any] | None:
    return _load_job(upload_id)
