import pandas as pd

file_path = "data/eod_records.csv"

df = pd.read_csv(file_path)

print("Total records:", len(df))

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head())

print("\nLocation count:")
print(df["location_name"].nunique())

print("\nLocations:")
print(df["location_name"].unique())