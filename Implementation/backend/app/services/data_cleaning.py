import pandas as pd

# datetime format
def _parse_datetime_series(s: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(s, format="%d/%m/%Y %I:%M:%S %p", errors="coerce")
    fallback = pd.to_datetime(s, errors="coerce")
    return parsed.fillna(fallback)

# cleaned raw data for ed_stay and stay_info tables
def clean_to_ed_stay_and_stay_info(df_raw: pd.DataFrame):
    """
    Returns (df_ed_stay, df_stay_info)
    df_ed_stay columns: stay_id, ed_timestamp, activity 
    df_stay_info columns: stay_id, gender, race, arrival_transport, disposition, chiefcomplaint, scale_level
    """
    # --- ed_stay table ---
    # select the required columns for ed_stay table
    needed_ed_stay = ["stay_id", "timestamps", "activity"]
    missing_ed_stay = [c for c in needed_ed_stay if c not in df_raw.columns]
    if missing_ed_stay:
        raise ValueError(f"Missing required columns for ed_stay: {missing_ed_stay}")

    df_ed_stay = df_raw[needed_ed_stay].copy()
    df_ed_stay["stay_id"] = pd.to_numeric(df_ed_stay["stay_id"], errors="coerce").astype("Int64")

    df_ed_stay["activity"]=(
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

    
    # change activity name to short one
    activity_mapping = {
    "enter the ed": "entry",
    "triage in the ed": "triage",
    "vital sign check": "vital",
    "medicine reconciliation": "medrecon",
    "medicine dispensations": "dispen",
    "discharge from the ed": "discharge"
    }

    df_ed_stay["activity"] = df_ed_stay["activity"].replace(activity_mapping)

    # --- stay_info table  ---
    # change the acuity column name as scale_level and extract first digit
    df_stay_info = df_raw[["stay_id",  "gender", "race", "arrival_transport", "disposition", "chiefcomplaint", "acuity"]].copy()
    df_stay_info = df_stay_info.rename(columns={"acuity": "scale_level"})
    df_stay_info["stay_id"] = pd.to_numeric(df_stay_info["stay_id"], errors="coerce").astype("Int64")
    
    df_stay_info["scale_level"] = (
    df_stay_info["scale_level"]
    .astype("string")
    .str.extract(r"(\d)")[0]  
    )
    # create a list of categorical columns to change data type
    cols_to_change = ["gender", "race", "arrival_transport", "disposition", "chiefcomplaint"]

    for col in cols_to_change:
        # Normalize stay_info text fields for consistent ingestion.
        df_stay_info[col] = (
            df_stay_info[col]
            .astype("string")
            .str.strip()
            .str.lower()
            .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA})
        )

    df_stay_info["scale_level"] = pd.to_numeric(df_stay_info["scale_level"], errors="coerce")
    
    # helper: first non-null value in a Series
    def first_non_null(s: pd.Series):
        s = s.dropna()
        return s.iloc[0] if len(s) else pd.NA

    # collapse to 1 row per stay_id
    df_stay_info = (
        df_stay_info.groupby("stay_id", as_index=False)
            .agg({
                "gender": first_non_null,
                "race": first_non_null,
                "arrival_transport": first_non_null,
                "disposition": first_non_null,
                "chiefcomplaint": first_non_null,
                "scale_level": first_non_null,
            })
    )
    
    df_stay_info = df_stay_info.dropna(
        subset=["stay_id", "gender", "race", "arrival_transport", "disposition", "chiefcomplaint", "scale_level"]
    )
    
    
            
    return df_ed_stay, df_stay_info
