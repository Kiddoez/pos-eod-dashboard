import streamlit as st
import pandas as pd
import plotly.express as px

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import (load_eod_records, load_backup_pauses)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
eod_df = load_eod_records()
pause_df = load_backup_pauses()


filtered_eod_df = eod_df.copy()
filtered_pause_df = pause_df.copy()
filtered_backup_location_df = eod_df.copy()


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
# LOCATION FILTER
# --------------------------------------------------

if selected_locations:

    filtered_eod_df = filtered_eod_df[
        filtered_eod_df["LocationName"].isin(selected_locations)
    ].copy()

    filtered_backup_location_df = filtered_backup_location_df[
        filtered_backup_location_df["LocationName"].isin(selected_locations)
    ].copy()


# --------------------------------------------------
# STATUS FILTER
# --------------------------------------------------

if selected_status == "EOD Problems":
    filtered_eod_df = filtered_eod_df[
        filtered_eod_df["EodProblem"] == True
    ].copy()

elif selected_status == "No EOD Problems":
    filtered_eod_df = filtered_eod_df[
        filtered_eod_df["EodProblem"] == False
    ].copy()


# --------------------------------------------------
# FILTERED BACKUP PERFORMANCE
# --------------------------------------------------

server_backup_df = (
    filtered_eod_df
    .groupby("ServerGroup", as_index=False)
    .agg(
        AvgBackupMinutes=("BackupDurationMinutes", "mean")
    )
    .sort_values(
        "AvgBackupMinutes",
        ascending=True,
    )
)

# --------------------------------------------------
# FILTER BACKUP INTERRUPTIONS
# --------------------------------------------------

selected_server_groups = set(
    filtered_backup_location_df["ServerGroup"].dropna()
)

# FILTER BY SELECTED SERVER GROUPS
if selected_locations:

    filtered_pause_df = filtered_pause_df[
        filtered_pause_df["ServerGroup"].isin(
            selected_server_groups
        )
    ].copy()

# DATE FILTER
filtered_pause_df = filtered_pause_df[
    (filtered_pause_df["ProcessDate"] >= selected_start)
    & (filtered_pause_df["ProcessDate"] < selected_end + pd.Timedelta(days=1))
].copy()



# --------------------------------------------------
# BACKUP ANALYSIS
# --------------------------------------------------

st.markdown(
    '<div class="section-label">Backup Analysis</div>',
    unsafe_allow_html=True,
)

st.info(
    "Backup interruption events are recorded at the server-group level. "
    "Locations that share the same server group will therefore show the "
    "same backup-event results."
)

col1, col2 = st.columns(2)

# --------------------------------------------------
# AVERAGE BACKUP DURATION BY SERVER GROUP
# --------------------------------------------------

with col1:

    with st.container(border=True):

        st.markdown(
            '<div class="card-title">Average Backup Duration by Server Group</div>',
            unsafe_allow_html=True,
        )

        if len(server_backup_df)>0:

            fig_backup_server = px.bar(
                server_backup_df,
                x="AvgBackupMinutes",
                y="ServerGroup",
                orientation="h",
                text="AvgBackupMinutes",
            )

            server_count = len(server_backup_df)

            if server_count == 1:
                bar_width = 0.25
            elif server_count == 2:
                bar_width = 0.45
            elif server_count <= 5:
                bar_width = 0.55
            else:
                bar_width = 0.75

            fig_backup_server.update_traces(
                width=bar_width
            )


            fig_backup_server.update_traces(
                texttemplate="%{text:.2f} min",
                textposition="outside",
                marker = dict(color="#1F4E79"),
            )

            fig_backup_server.update_layout(
                height=340,
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20,
                ),
                xaxis=dict(
                    title="Average Backup Duration (minutes)",
                    showgrid=True,
                    range=[
                        0,
                        server_backup_df["AvgBackupMinutes"].max() * 1.2
                    ],
                ),
                yaxis=dict(
                    title=None,
                    categoryorder="total ascending",
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_backup_server,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

        else:
            st.info("No records match the selected filters.")

# --------------------------------------------------
# BACKUP PAUSE DURATION
# --------------------------------------------------

with col2:

    with st.container(border=True):

        st.markdown(
            '<div class="card-title">Backup Interruption Duration</div>',
            unsafe_allow_html=True,
        )

        pause_analysis_df = filtered_pause_df.copy()

        if len(pause_analysis_df)>0:

            # Create 30-minute duration groups
            pause_bins = [0, 30, 60, 90, 120, 150, 180, 210, 240]

            pause_labels = [
                "0–29 min",
                "30–59 min",
                "60–89 min",
                "90–119 min",
                "120–149 min",
                "150–179 min",
                "180–209 min",
                "210–239 min",
            ]

            pause_analysis_df["PauseRange"] = pd.cut(
                pause_analysis_df["PauseDurationMinutes"],
                bins=pause_bins,
                labels=pause_labels,
                right=False,
            )

            pause_distribution = (
                pause_analysis_df
                .groupby(
                    "PauseRange",
                    observed=False,
                )
                .size()
                .reset_index(name="RecordCount")
            )

            fig_pause_duration = px.bar(
                pause_distribution,
                x="PauseRange",
                y="RecordCount",
                text="RecordCount",
            )

            fig_pause_duration.update_traces(
                texttemplate="%{text:,}",
                textposition="outside",
                marker = dict(color="#1F4E79"),
            )

            fig_pause_duration.update_layout(
                height=340,
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20,
                ),
                xaxis=dict(
                    title="Interruption Duration",
                    showgrid=False,
                ),
                yaxis=dict(
                    title="Number of Interruption Records",
                    showgrid=True,
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_pause_duration,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

        else:
            st.info("No records match the selected filters.")

# --------------------------------------------------
# BACKUP INTERRUPTION REASONS
# --------------------------------------------------

with st.container(border=True):

    st.markdown(
        """
            <div class="card-title">Backup Interruption Reasons</div>
            <div class="card-subtitle">Recorded reasons associated with backup interruptions</div>
        """,
        unsafe_allow_html=True,
    )

    reason_df = (
        filtered_pause_df["Reason"]
        .value_counts()
        .reset_index()
    )

    reason_df.columns = ["Reason", "RecordCount"]

    if len(reason_df)>0:

        fig_reasons = px.bar(
            reason_df,
            x="RecordCount",
            y="Reason",
            orientation="h",
            text="RecordCount",
        )

        fig_reasons.update_traces(
            textposition="outside",
            marker = dict(color="#1F4E79"),
        )

        fig_reasons.update_layout(
            height=200,
            margin=dict(
                l=20,
                r=60,
                t=20,
                b=20,
            ),
            xaxis=dict(
                title="Number of Interruption Records",
                showgrid=True,
            ),
            yaxis=dict(
                title=None,
                categoryorder="total ascending",
            ),
            showlegend=False,
            hovermode="closest",
        )

        st.plotly_chart(
            fig_reasons,
            use_container_width=True,
            config={
                "displayModeBar": False
            },
        )

    else:
        st.info("No records match the selected filters.")

# --------------------------------------------------
# BACKUP INTERRUPTION SUMMARY
# --------------------------------------------------

st.markdown(
    '<div class="card-title">Backup Interruption Summary</div>',
    unsafe_allow_html=True,
)

summary_col1, summary_col2, summary_col3 = st.columns(3)


interruption_count = len(filtered_pause_df)

if interruption_count > 0:

    avg_interruption = (filtered_pause_df["PauseDurationMinutes"].mean())

    longest_interruption = (filtered_pause_df["PauseDurationMinutes"].max())

else:

    avg_interruption = 0
    longest_interruption = 0


with summary_col1:

    st.metric(
        "Interruption Records",
        f"{interruption_count:,}"
    )


with summary_col2:

    st.metric(
        "Average Interruption",
        f"{avg_interruption:.2f} min"
    )


with summary_col3:

    st.metric(
        "Longest Interruption",
        f"{longest_interruption:,} min"
    )
