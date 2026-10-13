import pandas as pd

from src.database import get_engine


def load_daily_summary():
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

    return df


def load_server_performance():
    query = """
    SELECT
        ServerGroup,
        EodRecordCount,
        AvgEodMinutes,
        AvgBackupMinutes,
        LongestBackupMinutes,
        EodProblemCount,
        EodProblemRatePercent,
        TotalOfflineTransactions
    FROM dbo.vw_ServerGroupPerformance
    ORDER BY ServerGroup;
    """

    engine = get_engine()

    df = pd.read_sql(query, engine)

    engine.dispose()

    return df


def load_location_performance():
    query = """
    SELECT
        LocationID,
        StoreCode,
        LocationName,
        ServerGroup,
        RiskClass,
        EodRecordCount,
        AvgEodMinutes,
        AvgBackupMinutes,
        LongestBackupMinutes,
        EodProblemCount,
        EodProblemRatePercent,
        TotalOfflineTransactions
    FROM dbo.vw_LocationPerformance
    ORDER BY StoreCode;
    """

    engine = get_engine()

    df = pd.read_sql(query, engine)

    engine.dispose()

    return df

def load_backup_pauses():
    query = """
    SELECT
        ProcessDate,
        BackupID,
        ServerGroup,
        EventStart,
        EventEnd,
        PauseDurationMinutes,
        Reason
    FROM dbo.vw_BackupPauseAnalysis
    ORDER BY ProcessDate, EventStart;
    """

    engine = get_engine()

    df = pd.read_sql(query, engine)

    engine.dispose()

    df["ProcessDate"] = pd.to_datetime(df["ProcessDate"])
    df["EventStart"] = pd.to_datetime(df["EventStart"])
    df["EventEnd"] = pd.to_datetime(df["EventEnd"])

    return df

def load_offline_transactions():
    query = """
    SELECT
        StoreCode,
        LocationName,
        ServerGroup,
        OfflineBackupCases,
        TotalOfflineTransactions,
        AvgOfflineTransactions,
        MaxOfflineTransactions
    FROM dbo.vw_OfflineTransactionSummary
    ORDER BY TotalOfflineTransactions DESC;
    """

    engine = get_engine()

    df = pd.read_sql(query, engine)

    engine.dispose()

    return df

def load_kpi_summary():
    query = """
    SELECT
        COUNT(*) AS TotalEodRecords,

        SUM(
            CASE
                WHEN EodProblem = 1 THEN 1
                ELSE 0
            END
        ) AS EodProblemCount,

        CAST(
            100.0 *
            SUM(
                CASE
                    WHEN EodProblem = 1 THEN 1
                    ELSE 0
                END
            )
            / COUNT(*)
            AS DECIMAL(10,2)
        ) AS EodProblemRatePercent,

        AVG(
            CAST(
                DATEDIFF(MINUTE, EodStart, EodEnd)
                AS DECIMAL(10,2)
            )
        ) AS AvgEodMinutes,

        AVG(
            CAST(BackupDurationMinutes AS DECIMAL(10,2))
        ) AS AvgBackupMinutes,

        MAX(BackupDurationMinutes) AS LongestBackupMinutes,

        SUM(OfflineTransactionsDueToBackup)
            AS TotalOfflineTransactions

    FROM dbo.EodRecords;
    """

    engine = get_engine()

    df = pd.read_sql(query, engine)

    engine.dispose()

    return df


def load_eod_online_analysis():
    query = """
    SELECT
        EodRecordID,
        ProcessDate,
        StoreCode,
        LocationName,
        ServerGroup,
        RiskClass,
        EodStart,
        EodEnd,
        EodDurationMinutes,
        EodProblem,
        OnlineUpdateStart,
        OnlineUpdateEnd,
        OnlineUpdateDurationMinutes,
        EodToOnlineGapMinutes,
        ExecutionOrder
    FROM dbo.vw_EodOnlineAnalysis
    ORDER BY ProcessDate, EodStart;
    """

    engine = get_engine()
    df = pd.read_sql(query, engine)
    engine.dispose()

    df["ProcessDate"] = pd.to_datetime(df["ProcessDate"])
    df["EodStart"] = pd.to_datetime(df["EodStart"])
    df["EodEnd"] = pd.to_datetime(df["EodEnd"])
    df["OnlineUpdateStart"] = pd.to_datetime(df["OnlineUpdateStart"])
    df["OnlineUpdateEnd"] = pd.to_datetime(df["OnlineUpdateEnd"])

    return df

def load_eod_records():
    query = """
    SELECT
        e.EodRecordID,
        e.ProcessDate,
        l.StoreCode,
        l.LocationName,
        l.ServerGroup,
        l.RiskClass,
        e.EodStart,
        e.EodEnd,
        e.EodProblem,
        e.BackupDurationMinutes,
        e.OfflineTransactionsDueToBackup
    FROM dbo.EodRecords AS e
    INNER JOIN dbo.Locations AS l
        ON e.LocationID = l.LocationID
    ORDER BY e.ProcessDate, e.EodStart;
    """

    engine = get_engine()
    df = pd.read_sql(query, engine)
    engine.dispose()

    df["ProcessDate"] = pd.to_datetime(df["ProcessDate"])
    df["EodStart"] = pd.to_datetime(df["EodStart"])
    df["EodEnd"] = pd.to_datetime(df["EodEnd"])

    return df


# --------------------------------------------------
# TESTING SECTION
# --------------------------------------------------

if __name__ == "__main__":

    daily_df = load_daily_summary()
    location_df = load_location_performance()
    server_df = load_server_performance()
    pause_df = load_backup_pauses()
    offline_df = load_offline_transactions()
    kpi_df = load_kpi_summary()
    eod_online_df = load_eod_online_analysis()
    eod_df = load_eod_records()

    print("Daily summary:", daily_df.shape)
    print("Location performance:", location_df.shape)
    print("Server performance:", server_df.shape)
    print("Backup pauses:", pause_df.shape)
    print("Offline transactions:", offline_df.shape)
    print("KPI summary:", kpi_df.shape)

    print("\nKPI summary:")
    print(kpi_df)

    print("\nEOD online analysis:")
    print(eod_online_df.head())

    print("EOD Records:", eod_df.shape)
