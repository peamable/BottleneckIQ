from sqlalchemy import text
from app.core.database import engine


# create staging tables for data validation and error checking before inserting the final tables 
create_ed_stay_staging = """
CREATE TABLE IF NOT EXISTS ed_stay_staging (
  stay_id BIGINT NULL,
  ed_timestamp DATETIME NULL,
  activity VARCHAR(255) NULL,
  batch_id VARCHAR(50) NULL,
  upload_id BIGINT NULL,
  ingested_at DATETIME NULL,
  INDEX idx_upload_id (upload_id),
  CONSTRAINT fk_ed_stay_upload FOREIGN KEY (upload_id) REFERENCES upload_history(upload_id) ON DELETE CASCADE
);
"""

create_stay_info_staging = """
CREATE TABLE IF NOT EXISTS stay_info_staging (
  stay_id BIGINT NULL,
  gender VARCHAR(10) NULL,
  race VARCHAR(255) NULL,
  arrival_transport VARCHAR(255) NULL,
  disposition VARCHAR(255) NULL,
  scale_level DOUBLE NULL,
  chiefcomplaint VARCHAR(255) NULL,
  batch_id VARCHAR(50) NULL,
  upload_id BIGINT NULL,
  ingested_at DATETIME NULL,
  INDEX idx_upload_id (upload_id),
  CONSTRAINT fk_stay_info_upload FOREIGN KEY (upload_id) REFERENCES upload_history(upload_id) ON DELETE CASCADE
);
"""

def ensure_staging_tables():
    with engine.begin() as conn:
      conn.execute(text(create_ed_stay_staging))
      conn.execute(text(create_stay_info_staging))

def reset_staging_batch(batch_id: str):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ed_stay_staging WHERE batch_id=:b"), {"b": batch_id})
        conn.execute(text("DELETE FROM stay_info_staging WHERE batch_id=:b"), {"b": batch_id})
