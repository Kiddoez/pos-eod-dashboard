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
# APPLY DATE FILTER
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


# --------------------------------------------------
# CALCULATE EOD DURATION
# --------------------------------------------------

filtered_eod_df["EodDurationMinutes"] = (
    filtered_eod_df["EodEnd"]
    - filtered_eod_df["EodStart"]
).dt.total_seconds() / 60

# --------------------------------------------------
# MONTHLY EOD ANALYSIS
# --------------------------------------------------

monthly_df = filtered_eod_df.copy()

monthly_df["ProcessDate"] = pd.to_datetime(
    monthly_df["ProcessDate"]
)

monthly_df["Month"] = (
    monthly_df["ProcessDate"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

monthly_df = (
    monthly_df
    .groupby("Month", as_index=False)
    .agg(
        EodProblemCount=("EodProblem", "sum"),
        AvgEodMinutes=("EodDurationMinutes", "mean"),
    )
)

monthly_df["MonthLabel"] = monthly_df["Month"].dt.strftime("%b")

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


# --------------------------------------------------
# OVERVIEW CHARTS
# --------------------------------------------------

st.markdown(
    '<div class="section-label">EOD Operations</div>',
    unsafe_allow_html=True,
)


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
        f"""<div class="kpi-card">
            <div class="kpi-label">Problem Rate</div>
            <div class="kpi-value">{problem_rate:.2f}%</div>
            <div class="kpi-description">Share of EOD records with problems</div>
        </div>""",
        unsafe_allow_html=True,
    )


with kpi4:

    st.markdown(
        f""" <div class="kpi-card">
            <div class="kpi-label">Average EOD Duration</div>
            <div class="kpi-value">{avg_eod:.2f} min</div>
            <div class="kpi-description">Average recorded duration</div>
        </div>""",
        unsafe_allow_html=True,

    )

# --------------------------------------------------
# MONTHLY EOD PROBLEMS
# --------------------------------------------------

chart1, chart2 = st.columns(2)

with chart1:

    with st.container(border=True):

        st.markdown(
            """
                <div class="card-title">MONTHLY EOD Problems</div>
                <div class="card-subtitle">Total recorded EOD problems by month</div>
            """,
            unsafe_allow_html=True,
        )

        if len(monthly_df)>0:
            fig_problem = px.bar(
                monthly_df,
                x="MonthLabel",
                y="EodProblemCount",
                text="EodProblemCount",

            )

            fig_problem.update_traces(
                textposition="outside",
                marker=dict(color="#1F4E79")
            )

            fig_problem.update_layout(
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
                yaxis_title="EOD Problems",
                showlegend=False,
                hovermode="x",
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

# --------------------------------------------------
# MONTHLY AVERAGE EOD DURATION
# --------------------------------------------------

with chart2:

    with st.container(border=True):

        st.markdown(
            """
                <div class="card-title">MONTHLY Average EOD Duration</div>
                <div class="card-subtitle">Average recorded EOD duration by month</div>
            """,
            unsafe_allow_html=True,
            )

        if len(monthly_df)>0:
            fig_duration = px.line(
                monthly_df,
                x="MonthLabel",
                y="AvgEodMinutes",
                markers=True,
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
                yaxis_title="Minutes",
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