import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import sys
from pathlib import Path


# --------------------------------------------------
# PROJECT PATH
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import (
    load_backup_pauses,
    load_eod_online_analysis,
    load_eod_records,
)
# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

eod_df = load_eod_records()
pause_df = load_backup_pauses()
eod_online_df = load_eod_online_analysis()

filtered_eod_df = eod_df.copy()
filtered_pause_df = pause_df.copy()


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

# --------------------------------------------------
# CALCULATE EOD DURATION
# --------------------------------------------------

filtered_eod_df["EodDurationMinutes"] = (
    filtered_eod_df["EodEnd"] - filtered_eod_df["EodStart"]
).dt.total_seconds() / 60


# --------------------------------------------------
# FILTERED LOCATION ANALYSIS
# --------------------------------------------------

filtered_location_df = (
    filtered_eod_df
    .groupby(
        ["StoreCode", "LocationName"],
        as_index=False
    )
    .agg(
        EodRecordCount=("EodRecordID", "count"),
        AvgEodMinutes=("EodDurationMinutes", "mean"),
        EodProblemCount=("EodProblem", "sum"),
        TotalOfflineTransactions=(
            "OfflineTransactionsDueToBackup",
            "sum",
        ),
    )
)

filtered_location_df["EodProblemRatePercent"] = (
    filtered_location_df["EodProblemCount"]
    / filtered_location_df["EodRecordCount"]
    * 100
)


# --------------------------------------------------
# FILTERED KPI CALCULATIONS
# --------------------------------------------------

total_eod = len(filtered_eod_df)

total_problems = int(filtered_eod_df["EodProblem"].sum())

problem_rate = ((total_problems / total_eod) * 100
    if total_eod > 0
    else 0
)

avg_eod = (
    filtered_eod_df["EodDurationMinutes"].mean()
    if total_eod > 0
    else 0
)

avg_backup = (
    filtered_eod_df["BackupDurationMinutes"].mean()
    if total_eod > 0
    else 0
)

offline_transactions = int(filtered_eod_df["OfflineTransactionsDueToBackup"].sum())

# --------------------------------------------------
# FILTERED PROCESS DATA
# --------------------------------------------------

# EOD → Online Update records
filtered_process_df = eod_online_df[
    eod_online_df["EodRecordID"].isin(
        filtered_eod_df["EodRecordID"]
    )
].copy()


# Recorded EOD First rate
if len(filtered_process_df) > 0:

    eod_first_count = int(
        filtered_process_df["ExecutionOrder"]
        .eq("EOD First")
        .sum()
    )

    eod_first_rate = (
        eod_first_count
        / len(filtered_process_df)
        * 100
    )

    avg_gap = (
        filtered_process_df[
            "EodToOnlineGapMinutes"
        ].mean()
    )

else:

    eod_first_count = 0
    eod_first_rate = 0
    avg_gap = 0


# --------------------------------------------------
# FILTER BACKUP INTTERUPTION
# --------------------------------------------------
selected_server_groups = set(
    filtered_eod_df["ServerGroup"].dropna()
)

if selected_server_groups:
    filtered_pause_df = filtered_pause_df[
        filtered_pause_df["ServerGroup"].isin(
            selected_server_groups
        )
    ].copy()
else:
    filtered_pause_df = filtered_pause_df.iloc[0:0].copy()


# --------------------------------------------------
# DATE RANGE FILTERING
# --------------------------------------------------

filtered_pause_df = filtered_pause_df[
    (filtered_pause_df["ProcessDate"] >= selected_start)
    & (filtered_pause_df["ProcessDate"] <= selected_end)
].copy()

backup_interruptions = len(filtered_pause_df)


# --------------------------------------------------
# MONTHLY EOD DURATION ANALYSIS
# --------------------------------------------------


monthly_duration_df = filtered_eod_df.copy()

monthly_duration_df["ProcessDate"] = pd.to_datetime(
    monthly_duration_df["ProcessDate"]
)

monthly_duration_df["Month"] = (
    monthly_duration_df["ProcessDate"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

monthly_duration_df = (
    monthly_duration_df
    .groupby("Month", as_index=False)
    .agg(
        AvgEodMinutes=("EodDurationMinutes", "mean"),
    )
)

monthly_duration_df["MonthLabel"] = (
    monthly_duration_df["Month"].dt.strftime("%b")
)

# --------------------------------------------------
# MONTHLY PROBLEM ANALYSIS
# --------------------------------------------------

monthly_problem_df = filtered_eod_df.copy()

monthly_problem_df["Month"] = (
    pd.to_datetime(monthly_problem_df["ProcessDate"])
    .dt.to_period("M")
    .dt.to_timestamp()
)

monthly_problem_df = (
    monthly_problem_df
    .groupby("Month", as_index=False)
    .agg(
        EodProblemCount=("EodProblem", "sum")
    )
)

monthly_problem_df["MonthLabel"] = (
    monthly_problem_df["Month"].dt.strftime("%b")
)

# --------------------------------------------------
# DONUT CHART HELPER
# --------------------------------------------------

def create_donut(value, center_text, label, accent_color):
    """
    Create a compact donut KPI chart.
    """

    value = max(0, min(float(value), 100))
    remainder = 100 - value

    fig = go.Figure(
        go.Pie(
            values=[value, remainder],
            labels=[label, "Remaining"],
            hole=0.72,
            sort=False,
            direction="clockwise",
            marker=dict(
                colors=[
                    accent_color,
                    "#E8EDF3",
                ],
                line=dict(
                    color="#FFFFFF",
                    width=2,
                ),
            ),
            textinfo="none",
            hovertemplate=(
                f"<b>{label}</b><br>"
                "%{value:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=100,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(
                text=center_text,
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(
                    size=18,
                    color="#17345F",
                    family="Arial",
                ),
            )
        ],

    )

    return fig

# --------------------------------------------------
# OVERVIEW DASHBOARD
# --------------------------------------------------

# --------------------------------------------------
# KPI ROW
# --------------------------------------------------

kpi1, kpi2, kpi3, kpi4 = st.columns(4)


with kpi1:

    st.markdown(
        f""" <div class="kpi-card">
            <div class="kpi-label">EOD Records</div>
            <div class="kpi-value">{total_eod:,}</div>
            <div class="kpi-description">Recorded EOD executions</div>
        </div>""",
        unsafe_allow_html=True,
    )


with kpi2:

    st.markdown(
        f""" <div class="kpi-card">
            <div class="kpi-label">EOD Problems</div>
            <div class="kpi-value">{total_problems:,}</div>
            <div class="kpi-description">Recorded problem cases</div>
        </div>""",
        unsafe_allow_html=True,
    )


with kpi3:

    st.markdown(
        f""" <div class="kpi-card">
            <div class="kpi-label">Average EOD</div>
            <div class="kpi-value">{avg_eod:.2f} min</div>
            <div class="kpi-description">Average recorded duration</div>
        </div>""",
        unsafe_allow_html=True,
    )


with kpi4:

    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-label">Average Backup</div>
            <div class="kpi-value">{avg_backup:.2f} min</div>
            <div class="kpi-description">Average recorded duration</div>
        </div>""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# MAIN DASHBOARD ROW
# --------------------------------------------------

st.markdown(
    '<div class="dashboard-section-label">'
    'OPERATIONS'
    '</div>',
    unsafe_allow_html=True,
)

main_col1, main_col2 = st.columns([1.2,1])


# ==================================================
# EOD PROBLEMS
# ==================================================

with main_col1:

    with st.container(border=True):

        st.markdown(
            """<div class="card-title">EOD Problems</div>
                <div class="card-subtitle">Monthly recorded problem cases</div>
            """,
            unsafe_allow_html=True,
        )

        if len(monthly_problem_df)>0:
            fig_problem = px.bar(
                monthly_problem_df,
                x="MonthLabel",
                y="EodProblemCount",
                text="EodProblemCount",
            )


            fig_problem.update_traces(
                textposition="outside",
                cliponaxis=False,
                marker=dict(
                    color="#1F4E79"
                ),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "EOD Problems: %{y:,}"
                    "<extra></extra>"
                ),
            )

            fig_problem.update_layout(
                height=202,
                margin=dict(
                    l=10,
                    r=20,
                    t=10,
                    b=10,
                ),
                xaxis=dict(
                    title=None,
                    type="category",
                    showgrid=False,
                ),
                yaxis=dict(
                    title=None,
                    showgrid=True,
                    gridcolor="#E7EDF4",
                ),
            )

            st.plotly_chart(
                fig_problem,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )
        else:
            st.info("No records match the selected filters.")


# ==================================================
# OPERATIONAL SNAPSHOT
# ==================================================

with main_col2:

    with st.container(border=True):

        st.markdown(
            f"""<div class="card-title">Operational Snapshot</div>
                <div class="card-subtitle">Key indicators from the selected records</div>
            """,
            unsafe_allow_html=True,
        )


        # --------------------------------------------------
        # DONUTS
        # --------------------------------------------------

        donut1, donut2, donut3 = st.columns(3)


        problem_free_rate = (100 - problem_rate)

        with donut1:

            fig_problem_free = create_donut(
                problem_free_rate,
                f"{problem_free_rate:.1f}%",
                "Problem-Free",
                "#155EAD",
            )

            st.plotly_chart(
                fig_problem_free,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                },
            )

            st.markdown(
                """
                <div class="donut-label">
                    Problem-Free
                </div>
                """,
                unsafe_allow_html=True,
            )


        # Recorded EOD First
        with donut2:

            fig_eod_first = create_donut(
                eod_first_rate,
                f"{eod_first_rate:.0f}%",
                "Recorded EOD First",
                "#268A62",
            )

            st.plotly_chart(
                fig_eod_first,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

            st.markdown(
                """
                <div class="donut-label">
                    EOD First
                </div>
                """,
                unsafe_allow_html=True,
            )


        # EOD Problem Rate
        with donut3:

            fig_problem_rate = create_donut(
                problem_rate,
                f"{problem_rate:.1f}%",
                "EOD Problem",
                    "#D56756",
            )

            st.plotly_chart(
                fig_problem_rate,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

            st.markdown(
                """
                <div class="donut-label">
                    Problem Rate
                </div>
                """,
                unsafe_allow_html=True,
            )


        # --------------------------------------------------
        # MINI METRICS
        # --------------------------------------------------

        st.markdown(
            '<div class="snapshot-divider"></div>',
            unsafe_allow_html=True,
        )


        snapshot1, snapshot2, snapshot3 = st.columns(3)


        with snapshot1:

            st.markdown(
                f"""<div class="mini-stat">
                    <div class="mini-stat-label">Backup Interruptions</div>
                    <div class="mini-stat-value">{backup_interruptions:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


        with snapshot2:

            st.markdown(
                f"""<div class="mini-stat"><div class="mini-stat-label">Avg EOD → Online</div>
                <div class="mini-stat-value">{avg_gap:.2f} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


        with snapshot3:

            st.markdown(
                f"""<div class="mini-stat">
                    <div class="mini-stat-label">Offline Transactions</div>
                    <div class="mini-stat-value">{offline_transactions:,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# --------------------------------------------------
# SECOND ROW
# --------------------------------------------------

st.markdown(
    '<div class="dashboard-section-label">'
    'DETAIL SNAPSHOT'
    '</div>',
    unsafe_allow_html=True,
)

bottom_col1, bottom_col2 = st.columns([1,1.3])


# ==================================================
# LOCATION SNAPSHOT
# ==================================================

with bottom_col1:

    with st.container(border=True):

        st.markdown(
            """
            <div class="card-title">
                Location Snapshot
            </div>

            <div class="card-subtitle">
                Recorded performance across selected locations
            </div>
            """,
            unsafe_allow_html=True,
        )


        location_snapshot = (
            filtered_location_df
            .sort_values(
                "EodProblemCount",
                ascending=False,
            )
            .head(5)
            .copy()
        )

        if len(location_snapshot) > 0:

            location_display = (
                location_snapshot[
                    [
                        "LocationName",
                        "EodRecordCount",
                        "AvgEodMinutes",
                        "EodProblemCount",
                        "EodProblemRatePercent",
                    ]
                ]
                .rename(
                    columns={
                        "LocationName": "Location",
                        "EodRecordCount": "Records",
                        "AvgEodMinutes": "Avg EOD",
                        "EodProblemCount": "Problems",
                        "EodProblemRatePercent": "Rate",
                    }
                )
            )


            location_display["Avg EOD"] = (
                location_display["Avg EOD"]
                .map(
                    lambda x: f"{x:.2f} min"
                )
            )

            location_display["Rate"] = (
                location_display["Rate"]
                .map(
                    lambda x: f"{x:.2f}%"
                )
            )


            st.dataframe(
                location_display,
                use_container_width=True,
                hide_index=True,
                height=225,
            )

        else:

            st.info("No records match the selected filters.")

# ==================================================
# PROCESS TIMING
# ==================================================


with bottom_col2:

    with st.container(border=True):

        st.markdown(
            """
            <div class="card-title">
                Process Timing
            </div>

            <div class="card-subtitle">
                Recorded EOD → Online Update Gap
            </div>
            """,
            unsafe_allow_html=True,
        )


        gap_df = (
            filtered_process_df
            .groupby(
                "EodToOnlineGapMinutes"
            )
            .size()
            .reset_index(
                name="RecordCount"
            )
            .sort_values(
                "EodToOnlineGapMinutes"
            )
        )


        if len(gap_df) > 0:

            fig_gap = px.bar(
                gap_df,
                x="RecordCount",
                y="EodToOnlineGapMinutes",
                orientation="h",
                text="RecordCount",
            )


            fig_gap.update_traces(
                texttemplate="%{text:,}",
                textposition="outside",
                cliponaxis=False,
                marker=dict(
                    color="#1F4E79"
                ),
                hovertemplate=(
                    "<b>%{y} minute gap</b><br>"
                    "Records: %{x:,}"
                    "<extra></extra>"
                ),
            )


            fig_gap.update_layout(
                height=225,
                margin=dict(
                    l=10,
                    r=55,
                    t=5,
                    b=10,
                ),
                xaxis=dict(
                    title=None,
                    showgrid=True,
                    gridcolor="#E7EDF4",
                ),
                yaxis=dict(
                    title=None,
                    dtick=1,
                    autorange="reversed",
                ),
            )


            st.plotly_chart(
                fig_gap,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

        else:
            st.info("No records match the selected filters.")


# --------------------------------------------------
# EOD DURATION + BACKUP PERFORMANCE
# --------------------------------------------------
st.markdown(
    '<div class="dashboard-section-label">PROCESS PERFORMANCE</div>',
    unsafe_allow_html=True,
)

duration_col, backup_col = st.columns(2)


# --------------------------------------------------
# EOD DURATION
# --------------------------------------------------

with duration_col:

    with st.container(border=True):

        st.markdown(
            """
            <div class="card-title">
                EOD Duration
            </div>

            <div class="card-subtitle">
                Average recorded EOD duration by month
            </div>
            """,
            unsafe_allow_html=True,
        )

# ----------------------------------------------
# CREATE CHART
# ----------------------------------------------
        if len(monthly_duration_df)>0:
            fig_duration = px.line(
                monthly_duration_df,
                x="MonthLabel",
                y="AvgEodMinutes",
                markers=True,
            )

            fig_duration.update_traces(
            marker=dict(
                color="#2F75B5"
                )
            )

            fig_duration.update_layout(
                height=300,
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20,
                ),
                xaxis=dict(
                    tickangle=0,
                    type="category",
                ),
                xaxis_title=None,
                yaxis_title=None,
                showlegend=False,
                hovermode="x",
            )

            st.plotly_chart(
                fig_duration,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )
        else:
            st.info("No records match the selected filters.")

# --------------------------------------------------
# BACKUP PERFORMANCE
# --------------------------------------------------

with backup_col:

    with st.container(border=True):

        st.markdown(
            """
            <div class="card-title">
                Backup Performance
            </div>

            <div class="card-subtitle">
                Average recorded backup duration by server group
            </div>
            """,
            unsafe_allow_html=True,
        )

        backup_performance_df = (
            filtered_eod_df
            .groupby(
                "ServerGroup",
                as_index=False
            )
            .agg(
                AvgBackupMinutes=(
                    "BackupDurationMinutes",
                    "mean"
                )
            )
            .sort_values(
                "AvgBackupMinutes",
                ascending=True,
            )
        )

        if len(backup_performance_df)>0:

            fig_backup = px.bar(
                backup_performance_df,
                x="AvgBackupMinutes",
                y="ServerGroup",
                orientation="h",
                text="AvgBackupMinutes",
            )

            fig_backup.update_traces(
                texttemplate="%{text:.2f} min",
                textposition="outside",
                cliponaxis=False,
                marker=dict(color="#1F4E79"),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Average Backup: %{x:.2f} min"
                    "<extra></extra>"
                ),
            )

            fig_backup.update_layout(
                height=300,
                margin=dict(
                    l=20,
                    r=80,
                    t=15,
                    b=20,
                ),
                xaxis=dict(
                    title=None,
                    showgrid=True,
                ),
                yaxis=dict(
                    title=None,
                    categoryorder="total ascending",
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_backup,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )
        else:
            st.info("No records match the selected filters.")