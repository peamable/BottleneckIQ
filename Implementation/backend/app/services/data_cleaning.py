import pandas as pd

# datetime format
def _parse_datetime_series(s: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(s, format="%d/%m/%Y %I:%M:%S %p", errors="coerce")
    fallback = pd.to_datetime(s, errors="coerce")
    return parsed.fillna(fallback)

# cleaned raw data for ed_stay and acuity tables
def clean_to_ed_stay_and_acuity(df_raw: pd.DataFrame):
    """
    Returns (df_ed_stay, df_acuity)
    df_ed_stay columns: stay_id, ed_timestamp, activity
    df_acuity columns: stay_id, scale_level
    """
    # --- ed_stay table ---
    # select the required columns for ed_stay table
    needed_ed_stay = ["stay_id", "timestamps", "activity"]
    missing_ed_stay = [c for c in needed_ed_stay if c not in df_raw.columns]
    if missing_ed_stay:
        raise ValueError(f"Missing required columns for ed_stay: {missing_ed_stay}")

    df_ed_stay = df_raw[needed_ed_stay].copy()
    df_ed_stay["stay_id"] = pd.to_numeric(df_ed_stay["stay_id"], errors="coerce").astype("Int64")
    df_ed_stay["activity"] = (
        df_ed_stay["activity"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    # change timestamps named as ed_timestamp and datetime format
    # drop the timestamps column
    df_ed_stay["ed_timestamp"] = _parse_datetime_series(df_ed_stay["timestamps"])
    df_ed_stay = df_ed_stay.drop(columns=["timestamps"])

     # sort by timestamp
     # remove duplicate with same activity with same stay_id and keep earliest per stay_id + activity
    df_ed_stay = df_ed_stay.sort_values("ed_timestamp")
    df_ed_stay = df_ed_stay.drop_duplicates(subset=["stay_id", "activity"], keep="first")

    df_ed_stay["activity"] = (
    df_ed_stay["activity"]
        .str.strip()
        .str.lower()
    )

    # changing activity name to short one
    activity_mapping = {
    "enter the ed": "entry",
    "triage in the ed": "triage",
    "vital sign check": "vital",
    "medicine reconciliation": "medrecon",
    "medicine dispensations": "dispen",
    "discharge from the ed": "discharge"
    }

    df_ed_stay["activity"] = df_ed_stay["activity"].replace(activity_mapping)

    # --- acuity table  ---
    # change the acuity column name as scale_level and extract first digit
    df_acuity = df_raw[["stay_id", "acuity"]].copy()
    df_acuity = df_acuity.rename(columns={"acuity": "scale_level"})
    df_acuity["stay_id"] = pd.to_numeric(df_acuity["stay_id"], errors="coerce").astype("Int64")
    
    df_acuity["scale_level"] = (
    df_acuity["scale_level"]
    .astype(str)
    .str.extract(r"(\d)")  
    )

    df_acuity["scale_level"] = pd.to_numeric(df_acuity["scale_level"], errors="coerce")
    df_acuity = df_acuity.dropna(subset=["stay_id", "scale_level"])
    df_acuity = df_acuity.drop_duplicates(subset=["stay_id"], keep="first")
    
            
    return df_ed_stay, df_acuity