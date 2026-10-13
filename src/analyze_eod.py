import pandas as pd

file_path = "data/eod_records.csv"

df = pd.read_csv(file_path)

# Convert text columns into datetime values
datetime_columns = [
    "eod_start",
    "eod_end",
    "online_update_start",
    "online_update_end",
    "backup_start",
    "backup_end",
]

for column in datetime_columns:
    df[column] = pd.to_datetime(df[column])

# Calculate durations
df["calculated_eod_minutes"] = (
    df["eod_end"] - df["eod_start"]
).dt.total_seconds() / 60

df["calculated_online_update_minutes"] = (
    df["online_update_end"] - df["online_update_start"]
).dt.total_seconds() / 60

df["calculated_backup_minutes"] = (
    df["backup_end"] - df["backup_start"]
).dt.total_seconds() / 60

print("Average EOD duration:")
print(round(df["calculated_eod_minutes"].mean(), 2), "minutes")

print("\nAverage online update duration:")
print(round(df["calculated_online_update_minutes"].mean(), 2), "minutes")

print("\nAverage backup duration:")
print(round(df["calculated_backup_minutes"].mean(), 2), "minutes")

print("\nLongest backup:")
print(round(df["calculated_backup_minutes"].max(), 2), "minutes")

print("\nEOD records longer than 3 minutes:")
print(
    df[df["calculated_eod_minutes"] > 3][
        [
            "process_date",
            "location_name",
            "eod_start",
            "eod_end",
            "calculated_eod_minutes",
        ]
    ].head(10)
)