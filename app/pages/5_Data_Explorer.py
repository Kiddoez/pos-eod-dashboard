import streamlit as st
import pandas as pd

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_eod_records


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

eod_df = load_eod_records()

filtered_eod_df = eod_df.copy()


# --------------------------------------------------
# SHARED FILTER VALUES
# --------------------------------------------------

selected_start_date = st.session_state.selected_start_date
selected_end_date = st.session_state.selected_end_date
selected_locations = st.session_state.selected_locations
selected_status = st.session_state.status_filter


# --------------------------------------------------
# DATE FILTER
# --------------------------------------------------

selected_start = pd.Timestamp(selected_start_date).normalize()
selected_end = pd.Timestamp(selected_end_date).normalize()

filtered_eod_df["ProcessDate"] = pd.to_datetime(filtered_eod_df["ProcessDate"])

filtered_eod_df = filtered_eod_df[
    (filtered_eod_df["ProcessDate"] >= selected_start)
    & (filtered_eod_df["ProcessDate"] < selected_end + pd.Timedelta(days=1))
].copy()

# --------------------------------------------------
# APPLY LOCATION FILTER
# --------------------------------------------------

if selected_locations:

    filtered_eod_df = filtered_eod_df[
        filtered_eod_df["LocationName"].isin(selected_locations)
    ].copy()

# --------------------------------------------------
# APPLY STATUS FILTER
# --------------------------------------------------

if selected_status == "EOD Problems":
    filtered_eod_df = filtered_eod_df[
        filtered_eod_df["EodProblem"] == True
    ].copy()

elif selected_status == "No EOD Problems":
    filtered_eod_df = filtered_eod_df[
        filtered_eod_df["EodProblem"] == False
    ].copy()


st.caption(
    f"Showing {len(filtered_eod_df):,} records"
)

# --------------------------------------------------
# PREPARE TABLE
# --------------------------------------------------
display_columns = [
    "ProcessDate",
    "StoreCode",
    "LocationName",
    "ServerGroup",
    "RiskClass",
    "EodStart",
    "EodEnd",
    "EodProblem",
    "OnlineUpdateStart",
    "OnlineUpdateEnd",
    "BackupStart",
    "BackupEnd",
    "BackupDurationMinutes",
    "OfflineTransactionsDueToBackup",
]

display_df = filtered_eod_df[
    [column for column in display_columns if column in filtered_eod_df.columns]
].copy()


# --------------------------------------------------
# FORMAT TABLE
# --------------------------------------------------

if "ProcessDate" in display_df.columns:
    display_df["ProcessDate"] = pd.to_datetime(
        display_df["ProcessDate"]
    ).dt.strftime("%Y-%m-%d")


if "EodProblem" in display_df.columns:
    display_df["EodProblem"] = display_df["EodProblem"].map(
        {
            False: "No",
            True: "Yes",
        }
    )


display_df = display_df.rename(
    columns={
        "ProcessDate": "Process Date",
        "StoreCode": "Store Code",
        "LocationName": "Location",
        "ServerGroup": "Server Group",
        "RiskClass": "Risk Class",
        "EodStart": "EOD Start",
        "EodEnd": "EOD End",
        "EodProblem": "EOD Problem",
        "OnlineUpdateStart": "Online Update Start",
        "OnlineUpdateEnd": "Online Update End",
        "BackupStart": "Backup Start",
        "BackupEnd": "Backup End",
        "BackupDurationMinutes": "Backup Duration (min)",
        "OfflineTransactionsDueToBackup": "Offline Transactions",
    }
)

# --------------------------------------------------
# DATA TABLE
# --------------------------------------------------

if filtered_eod_df.empty:

    st.info(
        "No records match the selected filters."
    )

else:
    # CSV EXPORT
    csv_data = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name="pos_eod_filtered_records.csv",
        mime="text/csv",
    )


    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
