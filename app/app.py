import streamlit as st
import pandas as pd
import sys
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="POS EOD Operations Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS DESIGN
# ============================================================

def load_style():

    css_file = PROJECT_ROOT / "app" / "style" / "page.css"

    with open(css_file, "r", encoding="utf-8") as f:
        css = f.read()

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )


load_style()


# ============================================================
# LOAD DATA
# ============================================================

from src.data_loader import (
    load_daily_summary,
    load_location_performance,
)

daily_df = load_daily_summary()
location_df = load_location_performance()


# ============================================================
# PAGE DEFINITIONS
# ============================================================

dashboard = st.Page(
    "pages/Overview.py",
    title="Dashboard",
    icon=":material/dashboard:",
    default=True,
)

eod_performance = st.Page(
    "pages/1_EOD_Performance.py",
    title="EOD Performance",
    icon=":material/timer:",
)

backup_events = st.Page(
    "pages/2_Backup_Events.py",
    title="Backup Events",
    icon=":material/storage:",
)

location_analysis = st.Page(
    "pages/3_Location_Analysis.py",
    title="Location Analysis",
    icon=":material/location_on:",
)

process_analysis = st.Page(
    "pages/4_Process_Analysis.py",
    title="Process Analysis",
    icon=":material/account_tree:",
)

data_explorer = st.Page(
    "pages/5_Data_Explorer.py",
    title="Data Explorer",
    icon=":material/table_view:",
)


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div class="sidebar-brand">
            <div class="sidebar-brand-title">🛍️ POS EOD</div>
            <div class="sidebar-brand-subtitle">Operations Dashboard</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("Operational Monitoring")

        st.markdown(
            """
            <div class="sidebar-data-source">DATA SOURCE</div>
            """,
            unsafe_allow_html=True,
        )

        st.code(
            "SQL Server",
            language=None,
        )

        st.caption("© 2026 Felix Valdez")

render_sidebar()


# ============================================================
# NAVIGATION
# ============================================================

pg = st.navigation(
    {
        "Overview": [
            dashboard,
        ],

        "Analysis": [
            eod_performance,
            backup_events,
            location_analysis,
            process_analysis,
        ],

        "Data": [
            data_explorer,
        ],
    }
)

st.logo(image="🛍️", size="large", icon_image="🛍️")

# ============================================================
# PAGE HEADER
# ============================================================

PAGE_HEADERS = {

    "Dashboard": {
        "title": "POS EOD Operations Dashboard",
        "subtitle": (
            "Overview of recorded EOD, backup, and process "
            "performance across retail locations"
        ),
    },

    "EOD Performance": {
        "title": "EOD Performance",
        "subtitle": (
            "Analyze EOD execution time, problems, and "
            "performance trends across locations"
        ),
    },

    "Backup Events": {
        "title": "Backup Events",
        "subtitle": (
            "Analyze recorded backup interruptions and "
            "their associated event durations"
        ),
    },

    "Location Analysis": {
        "title": "Location Analysis",
        "subtitle": (
            "Compare EOD, backup, and operational performance "
            "across retail locations"
        ),
    },

    "Process Analysis": {
        "title": "Process Analysis",
        "subtitle": (
            "Analyze the recorded sequence and timing "
            "between EOD completion and online update"
        ),
    },

    "Data Explorer": {
        "title": "Data Explorer",
        "subtitle": (
            "Explore and inspect the underlying EOD operational records"
        ),
    },
}


current_page_title = pg.title

page_header = PAGE_HEADERS.get(
    current_page_title,
    {
        "title": current_page_title,
        "subtitle": "",
    },
)


st.markdown(
    f'<div class="page-title">'
    f'{page_header["title"]}'
    f'</div>',
    unsafe_allow_html=True,
)


if page_header["subtitle"]:

    st.markdown(
        f'<div class="page-subtitle">'
        f'{page_header["subtitle"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

min_date = daily_df["ProcessDate"].min()
max_date = daily_df["ProcessDate"].max()

st.caption(
    f"Data available: "
    f"{min_date:%b %d, %Y} — "
    f"{max_date:%b %d, %Y}"
)

# ============================================================
# GLOBAL FILTERS
# ============================================================

st.markdown(
    '<div class="section-label">GLOBAL FILTERS</div>',
    unsafe_allow_html=True,
)


filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

st.divider()


# ============================================================
# START DATE
# ============================================================

with filter_col1:

    st.markdown(
        '<div class="filter-label">📅 Start Date</div>',
        unsafe_allow_html=True,
    )

    selected_start_date = st.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
        key="start_date_filter",
    )


# ============================================================
# END DATE
# ============================================================

with filter_col2:

    st.markdown(
        '<div class="filter-label">📅 End Date</div>',
        unsafe_allow_html=True,
    )

    selected_end_date = st.date_input(
        "End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
        key="end_date_filter",
    )

# ============================================================
# DATE WARNING
# ============================================================

if selected_start_date > selected_end_date:
    st.warning("Start Date must be on or before End Date.")

# ============================================================
# LOCATION
# ============================================================

with filter_col3:

    st.markdown(
        '<div class="filter-label">📍 Location</div>',
        unsafe_allow_html=True,
    )

    location_filter_df = (
        location_df[
            ["StoreCode", "LocationName"]
        ]
        .drop_duplicates()
        .sort_values("StoreCode")
        .copy()
    )

    location_options = (
        location_filter_df["StoreCode"].astype(str)
        + " — "
        + location_filter_df["LocationName"]
    ).tolist()

    selected_location_labels = st.multiselect(
        "Location",
        options=location_options,
        default=[],
        placeholder="Select locations",
        label_visibility="collapsed",
        key="location_filter",
    )

    selected_locations = location_filter_df.loc[
        (
            location_filter_df["StoreCode"].astype(str)
            + " — "
            + location_filter_df["LocationName"]
        ).isin(selected_location_labels),
        "LocationName",
    ].tolist()


# ============================================================
# STATUS
# ============================================================

with filter_col4:

    st.markdown(
        '<div class="filter-label">⚑ Status</div>',
        unsafe_allow_html=True,
    )

    selected_status = st.selectbox(
        "Status",
        [
            "All Records",
            "EOD Problems",
            "No EOD Problems",
        ],
        label_visibility="collapsed",
        key="status_filter",
    )


# ============================================================
# STORE FILTER VALUES IN SESSION STATE
# ============================================================

st.session_state["selected_start_date"] = selected_start_date

st.session_state["selected_end_date"] = selected_end_date

st.session_state["selected_locations"] = selected_locations

st.session_state["selected_status"] = selected_status


# ============================================================
# RUN SELECTED PAGE
# ============================================================


pg.run()