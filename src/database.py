
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL


SERVER = os.getenv("DB_SERVER", r"TOPE\SQLEXPRESS")
DATABASE = os.getenv("DB_NAME", "PosEodPortfolio")
DRIVER = os.getenv(
    "DB_DRIVER",
    "ODBC Driver 18 for SQL Server",
)


def get_engine():
    if not SERVER:
        raise ValueError(
            "DB_SERVER is not configured. "
            "Set it to your SQL Server instance name."
        )

    connection_url = URL.create(
        "mssql+pyodbc",
        host=SERVER,
        database=DATABASE,
        query={
            "trusted_connection": "yes",
            "driver": DRIVER,
            "TrustServerCertificate": "yes",
        },
    )

    return create_engine(connection_url)
