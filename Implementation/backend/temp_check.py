from app.core.database import engine
from sqlalchemy import text

# Exact query from the function
query = text("""
    SELECT
        disposition,
        COUNT(*) AS cnt,
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS pct
    FROM stay_info
    WHERE disposition IS NOT NULL AND disposition <> ''
    GROUP BY disposition
    ORDER BY pct DESC
""")

with engine.connect() as conn:
    rows = conn.execute(query).mappings().all()

print(f"Number of rows returned: {len(rows)}")
for row in rows:
    print(row)

# Build disposition_mix
disposition_mix = [
    {
        "type": r["disposition"],
        "percentage": float(round(r["pct"], 2))
    }
    for r in rows
]

print(f"Disposition mix: {disposition_mix}")