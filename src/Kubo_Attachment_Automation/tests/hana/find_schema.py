"""
FIND SCHEMA — one-off diagnostic.

Connects to HANA (same env vars as the main script: HANA_HOST,
HANA_PORT, HANA_USER, HANA_PASSWORD — HANA_DATABASE is ignored
here on purpose) and asks the server directly which schema
contains the ODLN table, instead of guessing.

Run once:
    python find_schema.py
"""

import os

from hdbcli import dbapi

connection = dbapi.connect(
    address=os.environ.get("HANA_HOST", ""),
    port=int(os.environ.get("HANA_PORT", "30015")),
    user=os.environ.get("HANA_USER", ""),
    password=os.environ.get("HANA_PASSWORD", ""),
)

cursor = connection.cursor()

cursor.execute(
    "SELECT SCHEMA_NAME, TABLE_NAME "
    "FROM TABLES "
    "WHERE TABLE_NAME = 'ODLN'"
)

rows = cursor.fetchall()

cursor.close()
connection.close()

if not rows:
    print(
        "No schema containing ODLN was found (or the SYSTEM "
        "user can't see it). May need to ask George directly."
    )
else:
    print("ODLN found in:")
    for schema_name, table_name in rows:
        print(f"  Schema: {schema_name}  |  Table: {table_name}")
