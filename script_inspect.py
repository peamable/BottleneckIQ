import os
import pandas as pd
os.chdir('c:/Users/amabl/Documents/GitHub/W26_4495_S2_PhoebeA')
fn = 'Modeling/ed_full_schema_1k.csv'
df = pd.read_csv(fn, nrows=5)
print('COLS:', df.columns.tolist())
print(df.head(3).to_dict(orient='records'))
