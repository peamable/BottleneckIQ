import pandas as pd
# 1. change the file location
input_csv  = "D:/preproject_chunk/input/mimicel.csv"
output_dir = "D:/preproject_chunk/output/"
target_rows = 2000
max_files = 10

def simple_export_chunks():
    # Load and Sort 
    print("Loading data...")
    df = pd.read_csv(input_csv)
    
    # Sort and RESET INDEX to fix the iloc error
    df = df.sort_values(['stay_id', 'timestamps']).reset_index(drop=True)
    
    start_pos = 0
    file_count = 1
    total_rows = len(df)

    while start_pos < total_rows and file_count <= max_files:
        # set the end point of the chunk
        end_pos = start_pos + target_rows
        
        if end_pos < total_rows:
            # use the stay_id for cut-off point
            last_stay_id = df.iloc[end_pos - 1]['stay_id']
            
            # Find the very last row index for that specific stay_id
            # to avoid cutting a patient in half of ed_stay process
            actual_end = df[df['stay_id'] == last_stay_id].index[-1] + 1
            end_pos = actual_end

        # make small size and Save
        chunk = df.iloc[start_pos:end_pos]
        filename = f"{output_dir}test_chunk_{file_count}.csv"
        chunk.to_csv(filename, index=False)
        
        print(f"Saved {filename} ({len(chunk)} rows)")
        
        # change the pointer to the end of the chunk saved
        start_pos = end_pos
        file_count += 1

    print("Chunking complete.")

# RUN
simple_export_chunks()