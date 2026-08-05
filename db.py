"""db.py — shared SQL connection helper for Sunwave dashboard builds.

Env vars required:
  SQL_SERVER        - Azure SQL server (e.g. myserver.database.windows.net)
  SQL_DATABASE      - Database name
  SQL_USER          - SQL login username
  SQL_PASSWORD      - SQL login password

Uses pyodbc with ODBC Driver 18 for SQL Server.
"""
import os
import pyodbc
import pandas as pd

def get_connection():
    server   = os.environ['SQL_SERVER']
    database = os.environ['SQL_DATABASE']
    user     = os.environ['SQL_USER']
    password = os.environ['SQL_PASSWORD']
    conn_str = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={user};'
        f'PWD={password};'
        f'Encrypt=yes;'
        f'TrustServerCertificate=no;'
        f'Connection Timeout=30;'
    )
    return pyodbc.connect(conn_str)


def read_view(view_name, conn=None):
    close = False
    if conn is None:
        conn = get_connection()
        close = True
    try:
        df = pd.read_sql(f'SELECT * FROM {view_name}', conn)
        print(f'  {view_name}: {len(df)} rows, {len(df.columns)} columns')
        return df
    finally:
        if close:
            conn.close()
