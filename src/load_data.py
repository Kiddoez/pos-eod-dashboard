import pandas as pd

from src.database import get_engine


query = """
SELECT
    ProcessDate,
    TotalEodRecords,
    EodProblemCount,
    AvgEodMinutes,
    LongestEodMinutes,
    AvgBackupMinutes,
    LongestBackupMinutes,
    TotalOfflineTransactions
FROM dbo.vw_EodDailySummary
ORDER BY ProcessDate;
"""


engine = get_engine()

df = pd.read_sql(query, engine)

engine.dispose()


df["ProcessDate"] = pd.to_datetime(df["ProcessDate"])


print("Data successfully loaded from SQL Server.")

print("\nFirst 5 rows:")
print(df.head())

print("\nDataFrame information:")
print(df.info())