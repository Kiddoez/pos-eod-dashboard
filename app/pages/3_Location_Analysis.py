import streamlit as st
import pandas as pd
import plotly.express as px

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
# LOCATION FILTER
# --------------------------------------------------

if selected_locations:

    filtered_eod_df = filtered_eod_df[
        filtered_eod_df["LocationName"].isin(selected_locations)
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
# CALCULATE EOD DURATION
# --------------------------------------------------

filtered_eod_df["EodDurationMinutes"] = (
    filtered_eod_df["EodEnd"]
    - filtered_eod_df["EodStart"]
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
    )
)

filtered_location_df["EodProblemRatePercent"] = (
    filtered_location_df["EodProblemCount"]
    / filtered_location_df["EodRecordCount"]
    * 100
)



# --------------------------------------------------
# 2 LOCATION ANALYSIS
# --------------------------------------------------

st.markdown(
    '<div class="section-label">Location Analysis</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

# --------------------------------------------------
# AVERAGE EOD DURATION BY LOCATION
# --------------------------------------------------
with col1:

    with st.container(border=True):

        st.markdown(
            """
            <div class="card-title">Average EOD Duration by Location</div>
            <div class="card-subtitle">Recorded average EOD duration across retail locations</div>
            """,
            unsafe_allow_html=True,
            )

        location_chart_df = filtered_location_df.copy()

        # Sort locations from highest to lowest average EOD duration
        location_chart_df = location_chart_df.sort_values(
            "AvgEodMinutes",
            ascending=False,
        )

        if len(location_chart_df)>0:

            fig_location = px.bar(
                location_chart_df,
                x="AvgEodMinutes",
                y="LocationName",
                orientation="h",
                text="AvgEodMinutes",
                hover_data={
                    "StoreCode": True,
                    "LocationName": False,
                    "AvgEodMinutes": ":.2f",
                },
            )

            fig_location.update_traces(
                texttemplate="%{text:.2f} min",
                textposition="outside",
                cliponaxis=False,
                marker = dict(color="#1F4E79"),
            )

            location_count = len(location_chart_df)

            chart_height = max(200, location_count * 28)

            fig_location.update_layout(
                height=chart_height,
                margin=dict(
                    l=20,
                    r=80,
                    t=20,
                    b=20,
                ),
                xaxis=dict(
                    title="Average EOD Duration (minutes)",
                    showgrid=True,
                ),
                yaxis=dict(
                    title=None,
                    categoryorder="total ascending",
                ),
                showlegend=False,
            )

            st.plotly_chart(
                fig_location,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )
        else:
            st.info("No records match the selected filters.")

# --------------------------------------------------
# EOD PROBLEM RATE BY LOCATION
# --------------------------------------------------
with col2:
    with st.container(border=True):

        st.markdown(
            """
            <div class="card-title">EOD Problem Rate by Location</div>
            <div class="card-subtitle">Recorded EOD problem rate across retail locations</div>
            """,
            unsafe_allow_html=True,
            )


        problem_rate_df = filtered_location_df.copy()

        # Sort from highest recorded problem rate to lowest
        problem_rate_df = problem_rate_df.sort_values(
            "EodProblemRatePercent",
            ascending=False,
        )

        if len(problem_rate_df)>0:

            fig_problem_rate = px.bar(
                problem_rate_df,
                x="EodProblemRatePercent",
                y="LocationName",
                orientation="h",
                text="EodProblemRatePercent",
                hover_data={
                    "StoreCode": True,
                    "LocationName": False,
                    "EodProblemCount": True,
                    "EodProblemRatePercent": ":.2f",
                },
            )

            fig_problem_rate.update_traces(
                texttemplate="%{text:.2f}%",
                textposition="outside",
                cliponaxis=False,
                marker = dict(color="#1F4E79"),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Store Code: %{customdata[0]}<br>"
                    "EOD Problems: %{customdata[1]}<br>"
                    "Problem Rate: %{x:.2f}%"
                    "<extra></extra>"
                ),
            )

            location_count = len(problem_rate_df)

            chart_height = max(200, location_count * 28)

            fig_problem_rate.update_layout(
                height=chart_height,
                margin=dict(
                    l=20,
                    r=80,
                    t=20,
                    b=20,
                ),
                xaxis=dict(
                    title="EOD Problem Rate (%)",
                    showgrid=True,
                ),
                yaxis=dict(
                    title=None,
                    categoryorder="total ascending",
                ),
                showlegend=False,
            )


            st.plotly_chart(
                fig_problem_rate,
                use_container_width=True,
                config={
                    "displayModeBar": False
                },
            )

        else:
            st.info("No records match the selected filters.")