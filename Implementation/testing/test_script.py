import pandas as pd

def analyze_csv_patient_flows(file_path):
    print(f"Loading data from {file_path}...")
    
    # Load your CSV
    df = pd.read_csv(file_path)

    # Ensure timestamps are actual datetime objects for proper sorting
    # Change 'ed_timestamp' to whatever your column name is
    df['ed_timestamp'] = pd.to_datetime(df['ed_timestamp'])

    # 1. Clean activity names
    df['activity'] = df['activity'].str.lower().str.strip()

    # 2. Sort by patient (stay_id) and time to ensure the sequence is correct
    df = df.sort_values(by=['stay_id', 'ed_timestamp'])

    # 3. Group by stay_id and join activities into a path string
    flow_df = df.groupby('stay_id')['activity'].apply(lambda x: ' -> '.join(x)).reset_index()
    flow_df.rename(columns={'activity': 'path'}, inplace=True)

    # 4. Count unique patterns
    pattern_counts = flow_df['path'].value_counts().reset_index()
    pattern_counts.columns = ['Sequence_Pattern', 'Occurrences']

    # 5. Calculate percentages
    total_stays = len(flow_df)
    pattern_counts['Percentage'] = (pattern_counts['Occurrences'] / total_stays * 100).round(2)

    print(f"\nAnalyzed {total_stays} unique patient stays.")
    print("\n--- Top 15 Most Common Patient Flow Patterns ---")
    print(pattern_counts.to_string(index=False))
    
    # Optional: Save results to see every single unique path found
    # pattern_counts.to_csv("path_analysis_results.csv", index=False)
    
    return pattern_counts

if __name__ == "__main__":
    # Update this with the path to your CSV file
    FILE_NAME = "C:/Users/Phoebe/Downloads/ed_stay (2).csv" 
    analyze_csv_patient_flows(FILE_NAME)