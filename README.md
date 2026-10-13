# POS EOD Operations Dashboard

A Python-based operations analytics dashboard for monitoring Point-of-Sale (POS) End-of-Day (EOD) processes, backup performance, and location-level operational trends.

## Overview

The POS EOD Operations Dashboard analyzes recorded EOD activities across multiple store locations. It transforms operational records into interactive visualizations to help identify process delays, backup interruptions, EOD problems, and locations that may require further investigation.

This project demonstrates the use of Python, SQL Server, data analysis, and interactive dashboard development for an operational monitoring use case.

## Key Features

- **EOD Performance Monitoring** — Review EOD processing duration and recorded problem cases.
- **Backup Event Analysis** — Examine backup completion, duration, and pause events.
- **Location Analysis** — Compare operational performance across locations and server groups.
- **Process Timing Analysis** — Analyze recorded timing intervals between EOD and online update activities.
- **Data Explorer** — Inspect operational records through interactive dashboard filters.
- **Custom Dashboard Styling** — Use CSS to customize the dashboard's visual appearance, spacing, typography, and layout.

## Technology Stack

- **Python** — Application logic and data processing.
- **Streamlit** — Interactive dashboard interface and multipage navigation.
- **Pandas** — Data manipulation, aggregation, and analysis.
- **Plotly** — Interactive charts and data visualizations.
- **CSS** — Custom dashboard styling and visual presentation.
- **Microsoft SQL Server Express** — Relational database for operational records.
- **SQLAlchemy** — Database connectivity and SQL execution support.
- **pyodbc** — ODBC connectivity between Python and SQL Server.
- **Git and GitHub** — Version control and source-code hosting.

### Development Tools

- **Visual Studio Code (VS Code)** — Optional editor for developing and maintaining the project.
- **SQL Server Management Studio (SSMS)** — Database management, SQL queries, and data validation.


## Architecture

The application retrieves operational data from Microsoft SQL Server and uses Python to process and present the results through a Streamlit interface.

The database contains three principal tables:

- `EodRecords` — Recorded EOD, online update, backup, and related operational information.
- `BackupEvents` — Recorded backup events, including starts, completions, and pauses.
- `Locations` — Location information used to associate operational records with stores and server groups.

Pandas supports data processing and aggregation, Plotly provides interactive visualizations, and CSS customizes the dashboard's appearance.

SQLAlchemy and pyodbc support the application's database connectivity to Microsoft SQL Server.

## Project Structure

```text
pos-eod-dashboard/
├── app/
│   ├── app.py
│   ├── pages/
│   │   ├── Overview.py
│   │   ├── 1_EOD_Performance.py
│   │   ├── 2_Backup_Events.py
│   │   ├── 3_Location_Analysis.py
│   │   ├── 4_Process_Analysis.py
│   │   └── 5_Data_Explorer.py
│   └── style/
│       └── page.css
├── src/
│   ├── data_loader.py
│   ├── database.py
│   ├── load_data.py
│   ├── analyze_eod.py
│   └── inspect_data.py
├── requirements.txt
├── .gitignore
└── README.md
```

*This is a representative structure. Verify the actual folders and files before finalizing this section.*

## Database Design

The application uses Microsoft SQL Server Express as its relational database. The `PosEodPortfolio` database contains three main tables, three staging tables, and six analytical views.

### Main Tables

| Table | Purpose | Primary Key |
|---|---|---|
| `dbo.EodRecords` | Stores EOD process records, timestamps, problem indicators, online update information, backup metrics, and offline transaction counts. | `EodRecordID` |
| `dbo.BackupEvents` | Stores backup event details, including event type, timestamps, server group, and pause reason. | `EventID` |
| `dbo.Locations` | Stores location identifiers, store codes, location names, server groups, and risk classifications. | `LocationID` |

### Staging Tables

The database also contains staging tables used in the data preparation workflow:

- `dbo.EodRecords_Staging`
- `dbo.BackupEvents_Staging`
- `dbo.Locations_Staging`

These are documented separately from the main analytical tables.

### Analytical Views

| View | Purpose |
|---|---|
| `dbo.vw_EodDailySummary` | Aggregates daily EOD record counts, problem counts, average and longest EOD durations, backup durations, and offline transaction totals. |
| `dbo.vw_BackupPauseAnalysis` | Extracts backup-pause events and calculates their duration in minutes. |
| `dbo.vw_EodOnlineAnalysis` | Combines EOD records with location information and calculates EOD duration, online update duration, the EOD-to-online gap, and execution order. |
| `dbo.vw_LocationPerformance` | Summarizes EOD and backup performance, problem rates, and offline transactions by location. |
| `dbo.vw_OfflineTransactionSummary` | Summarizes records with offline transactions attributed to backup, grouped by location and server group. |
| `dbo.vw_ServerGroupPerformance` | Aggregates EOD and backup metrics, problem rates, and offline transaction totals by server group. |

### Logical Relationships

The database does not currently have declared foreign-key constraints. However, the view definitions establish the following logical join:

`EodRecords.LocationID = Locations.LocationID`

This join is used by `vw_EodOnlineAnalysis`, `vw_LocationPerformance`, `vw_OfflineTransactionSummary`, and `vw_ServerGroupPerformance`.

The `vw_EodDailySummary` view aggregates records directly from `EodRecords`, while `vw_BackupPauseAnalysis` reads from `BackupEvents` and filters for events where `EventType = 'Backup paused'`.

### Data Flow

1. Operational records are prepared and stored in the main SQL Server tables.
2. SQL views perform aggregations, joins, calculations, and filtering.
3. Python retrieves and processes the required data.
4. Streamlit presents the results through interactive tables, metrics, filters, and visualizations.

## Prerequisites

- Python
- Microsoft SQL Server Express
- SQL Server Management Studio (SSMS)
- The configured `PosEodPortfolio` database
- The required database tables and views
- An installed ODBC driver compatible with the SQL Server connection configuration

## Local Setup

### 1. Open the project

Open the existing project directory in VS Code or another Python-compatible editor.

### 2. Create and activate a virtual environment

Run the following commands in Windows PowerShell from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the database connection

The application reads its database settings from environment variables.

| Variable | Description | Example |
|---|---|---|
| `DB_SERVER` | SQL Server instance name | `localhost\SQLEXPRESS` |
| `DB_NAME` | Database name | `PosEodPortfolio` |
| `DB_DRIVER` | Installed ODBC driver | `ODBC Driver 18 for SQL Server` |

Use `.env.example` as a reference for the required settings. The application does not automatically load `.env` files; the variables must be configured in your environment before running the dashboard.

For Git Bash, set the variables with:

```bash
export DB_SERVER='localhost\SQLEXPRESS'
export DB_NAME='PosEodPortfolio'
export DB_DRIVER='ODBC Driver 18 for SQL Server'
```

Replace the example server name with your own SQL Server instance. The database, required tables, and views must already exist, and Windows Trusted Connection authentication must be configured.

Do not commit `.env` files containing local settings or credentials.

### 5. Run the dashboard

From the project root:

```powershell
python -m streamlit run app/app.py
```

Open the local URL displayed in the terminal.

## Data Privacy

The dashboard was developed around operational EOD and backup records. Before publishing the repository, review the source code, configuration files, documentation, and datasets for confidential business information, personal information, internal network details, and production data.

Operational CSV files, database exports, credentials, and other sensitive material must not be committed unless they have been explicitly reviewed and approved for publication.

## Project Status

The current project version is intended for local execution using Microsoft SQL Server as its data source. A separate public-demo version may be developed independently.

## Future Improvements

- Improve data validation and error handling.
- Expand operational performance metrics.
- Enhance dashboard usability and visualization consistency.
- Develop a separate public demo using appropriately prepared demo data.

## Author

Developed as a portfolio project demonstrating Python data analysis, SQL Server integration, and interactive dashboard development.
