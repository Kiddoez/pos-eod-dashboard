import streamlit as st
import pandas as pd
import plotly.express as px

import sys
from pathlib import Path



PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_eod_online_analysis


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

process_df = load_eod_online_analysis()

filtered_process_df = process_df.copy()


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

filtered_process_df["ProcessDate"] = pd.to_datetime(filtered_process_df["ProcessDate"])

filtered_process_df = filtered_process_df[
    (filtered_process_df["ProcessDate"] >= selected_start)
    & (filtered_process_df["ProcessDate"] < selected_end + pd.Timedelta(days=1))
].copy()

# --------------------------------------------------
# APPLY LOCATION FILTER
# --------------------------------------------------

if selected_locations:

    filtered_process_df = filtered_process_df[
        filtered_process_df["LocationName"].isin(selected_locations)
    ].copy()

# --------------------------------------------------
# APPLY STATUS FILTER
# --------------------------------------------------

if selected_status == "EOD Problems":
    filtered_process_df = filtered_process_df[
        filtered_process_df["EodProblem"] == True
    ].copy()

elif selected_status == "No EOD Problems":
    filtered_process_df = filtered_process_df[
        filtered_process_df["EodProblem"] == False
    ].copy()



# --------------------------------------------------
# EOD → ONLINE UPDATE GAP
# --------------------------------------------------

st.markdown(
    '<div class="section-label">Online Update Analysis</div>',
    unsafe_allow_html=True,
)


gap, metrics, = st.columns([2, 1])

with gap:
    with st.container(border=True):

        st.markdown(
                """
                    <div class="card-title">EOD → Online Update Gap Distribution</div>
                    <div class="card-subtitle">Distribution of recorded time between EOD completion and online update start</div>
                """,
                unsafe_allow_html=True,
        )

        # --------------------------------------------------
        # EOD - ONLINE UPDATE GAP
        # --------------------------------------------------

        gap_df = (
            filtered_process_df
            .groupby("EodToOnlineGapMinutes")
            .size()
            .reset_index(name="RecordCount")
            .sort_values("EodToOnlineGapMinutes")
        )

        if len(gap_df)>0:
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
                marker = dict(color="#1F4E79"),
                hovertemplate=(
                    "<b>%{y} minute gap</b><br>"
                    "Records: %{x:,}"
                    "<extra></extra>"
                ),
            )

            fig_gap.update_layout(
                height=198,
                margin=dict(
                    l=20,
                    r=80,
                    t=20,
                    b=20,
                ),
                xaxis=dict(
                    title="Number of Records",
                    showgrid=True,
                ),
                yaxis=dict(
                    title="Gap After EOD (minutes)",
                    dtick=1,
                    autorange="reversed"
                ),
                showlegend=False,
                hovermode="closest",
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
# PROCESS GAP METRICS
# --------------------------------------------------

if len(filtered_process_df) > 0:

    avg_gap = filtered_process_df[
        "EodToOnlineGapMinutes"
    ].mean()

    min_gap = filtered_process_df[
        "EodToOnlineGapMinutes"
    ].min()

    max_gap = filtered_process_df[
        "EodToOnlineGapMinutes"
    ].max()

else:

    avg_gap = 0
    min_gap = 0
    max_gap = 0

with metrics:
    # --------------------------------------------------
    # GAP ANALYSIS
    # --------------------------------------------------

        st.metric(
            label="Average Gap",
            value=f"{avg_gap:.2f} min",
        )

        st.metric(
            "Shortest Gap",
            f"{min_gap:.0f} min"
        )

        st.metric(
            "Longest Gap",
            f"{max_gap:.0f} min"
        )



# --------------------------------------------------
# RECORDED EXECUTION ORDER METRIC CALCULATION
# --------------------------------------------------

execution_counts = (
    filtered_process_df["ExecutionOrder"].fillna("Unrecorded").astype(str).str.strip().replace("", "Unrecorded").value_counts()
)

eod_first_count = int(execution_counts.get("EOD First", 0))

total_execution_records = len(filtered_process_df)

other_count = total_execution_records - eod_first_count

eod_first_percent = (
    (eod_first_count / total_execution_records) * 100
    if total_execution_records > 0
    else 0
)

# --------------------------------------------------
# RECORDED EXECUTION ORDER
# --------------------------------------------------


st.markdown(
    """
        <div class="card-title">Recorded Execution</div>
        <div class="card-subtitle">Sequence of EOD completion and online update start based on recorded timestamps</div>
    """,
    unsafe_allow_html=True,
    )


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "EOD First",
        f"{eod_first_count:,}",
    )

with col2:
    st.metric(
        "Other Sequence",
        f"{other_count:,}",
    )

with col3:
    st.metric(
        "EOD First Rate",
        f"{eod_first_percent:.2f}%",
    )

if other_count == 0:
    st.info(
        "All recorded EOD records show EOD completion before the online update started."
    )


# --------------------------------------------------
# PROCESS TIMING BY SERVER GROUP
# --------------------------------------------------

st.markdown(
    '<div class="section-label">Process Timing by Server Group</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):

    st.markdown(
        """
            <div class="card-title">Timing by Server Group</div>
            <div class="card-subtitle">Average recorded duration for EOD, online update and the gap between them.</div>
        """,
        unsafe_allow_html=True,
        )


    server_process_df = (
        filtered_process_df
        .groupby("ServerGroup", as_index=False)
        .agg(
            AvgEodMinutes=("EodDurationMinutes", "mean"),
            AvgOnlineUpdateMinutes=("OnlineUpdateDurationMinutes", "mean"),
            AvgEodToOnlineGapMinutes=("EodToOnlineGapMinutes", "mean"),
            RecordCount=("EodRecordID", "count"),
        )
        .sort_values(
            "AvgEodToOnlineGapMinutes",
            ascending=False,
        )
    )

    server_process_chart_df = server_process_df.rename(
        columns={
            "AvgEodMinutes": "EOD",
            "AvgOnlineUpdateMinutes": "Online Update",
            "AvgEodToOnlineGapMinutes": "EOD → Online Gap",
        }
    )

    if len(server_process_chart_df)>0:

        fig_server_process = px.bar(
            server_process_chart_df,
            x="ServerGroup",
            y=[
                "EOD",
                "Online Update",
                "EOD → Online Gap",
            ],
            barmode="group",
            labels={
                "ServerGroup": "Server Group",
                "value": "Average Minutes",
                "variable": "Process",
            },
            text_auto=".2f",

            color_discrete_map={
            "EOD": "#1F4E79",
            "Online Update": "#2F75B5",
            "EOD → Online Gap": "#4F9D9D",
            },
        )

        fig_server_process.update_layout(
            height=450,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=80,
            ),
            xaxis=dict(
                title="Server Group",
                tickangle=-35,
            ),
            yaxis=dict(
                title="Average Duration (minutes)",
                showgrid=True,
            ),
            legend=dict(
                title="Process",
            ),
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_server_process,
            use_container_width=True,
            config={
                "displayModeBar": False
            },
        )

    else:
        st.info("No records match the selected filters.")

# --------------------------------------------------
# OPERATIONAL CONTEXT
# --------------------------------------------------

st.markdown(
    '<div class="section-label">Operational Context</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):

    st.markdown(
        '<div class="card-title">24/7 Server Group Context</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Some server groups support 24/7 operations. "
        "For these locations, the timing of EOD and online update "
        "is relevant to when POS operations can resume under the "
        "established operating procedure. The analysis above uses "
        "recorded timestamps from the dataset; operational activities "
        "such as cashier closing, cash take-out, and POS reopening are "
        "not directly represented as timestamped events in this dataset."
    )