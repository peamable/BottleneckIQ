from sqlalchemy import text
from app.core.database import engine


def get_disposition_mix() -> dict:
    # We query the permanent table 'stay_info'
    # Since we aren't using upload_id yet, we get the distribution of all processed records
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

    disposition_mix = [
        {
            "type": r["disposition"],
            "percentage": float(round(r["pct"], 2))
        }
        for r in rows
    ]

    return {"logistics_root_cause": {"disposition_mix": disposition_mix}}

def get_chief_complaint_insights(upload_id: int):
    # 1. FETCH: Grab the raw column from the DB
    query = text("""
        SELECT chiefcomplaint 
        FROM stay_info 
        WHERE upload_id = :u_id AND chiefcomplaint IS NOT NULL
    """)
    
    with engine.connect() as conn:
        # Convert the SQL result directly into a Pandas Series
        rows = conn.execute(query, {"u_id": upload_id}).scalars().all()
        complaints_series = pd.Series(rows)

    if complaints_series.empty:
        return []

    # 2. PROCESS: Split and Tally
    # We split by both commas and semicolons to be safe
    all_tokens = (
        complaints_series
        .str.replace(';', ',')
        .str.split(',')
        .explode()
        .str.strip()
        .str.lower()
    )

    # 3. CONSOLE LOGGING (The Part You Asked For)
    # Get the top 10 as a Series
    top_10 = all_tokens.value_counts().head(10)
    
    print("\n" + "="*30)
    print(f"TOP 10 COMPLAINTS (ID: {upload_id})")
    print("="*30)
    print(top_10)
    print("="*30 + "\n")

    # # 3. ANALYZE: Get Top 10 and format for Frontend
    # counts = all_tokens.value_counts().head(10)
    
    # # Convert to a list of dicts for the JSON response
    # # e.g., [{"complaint": "chest pain", "count": 150}, ...]
    # return [
    #     {"label": complaint, "value": count} 
    #     for complaint, count in counts.items()

    # 2. This part allows you to run 'python insights_service.py' in your terminal
if __name__ == "__main__":
    # Put an ID you know exists in your database here
    get_chief_complaint_insights(upload_id=8)
    # ]