import os
from hdbcli import dbapi

conn = dbapi.connect(
    address=os.environ["HANA_HOST"],
    port=int(os.environ["HANA_PORT"]),
    user=os.environ["HANA_USER"],
    password=os.environ["HANA_PASSWORD"],
)

cur = conn.cursor()
cur.execute(
    "SELECT TABLE_NAME FROM TABLES "
    "WHERE SCHEMA_NAME = 'IAL01_DEV' "
    "AND UPPER(TABLE_NAME) LIKE '%TRUCK%'"
)

for row in cur.fetchall():
    print(row)

conn.close()
