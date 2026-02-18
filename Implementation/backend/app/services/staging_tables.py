from sqlalchemy import text
from app.core.database import engine


# create staging tables for data validation and error checking before inserting the final tables 
create_ed_stay_staging = """
CREATE TABLE IF NOT EXISTS ed_stay_staging (
  stay_id BIGINT NULL,
  ed_timestamp DATETIME NULL,
  activity VARCHAR(255) NULL,
  batch_id VARCHAR(50) NULL,
  ingested_at DATETIME NULL
);
"""

create_acuity_staging = """
CREATE TABLE IF NOT EXISTS acuity_staging (
  stay_id BIGINT NULL,
  scale_level DOUBLE NULL,
  batch_id VARCHAR(50) NULL,
  ingested_at DATETIME NULL
);
"""

def ensure_staging_tables():
    with engine.begin() as conn:
      conn.execute(text(create_ed_stay_staging))
      conn.execute(text(create_acuity_staging))

def reset_staging_batch(batch_id: str):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ed_stay_staging WHERE batch_id=:b"), {"b": batch_id})
        conn.execute(text("DELETE FROM acuity_staging WHERE batch_id=:b"), {"b": batch_id})
