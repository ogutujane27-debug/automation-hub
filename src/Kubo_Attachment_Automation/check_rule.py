import os
from dotenv import load_dotenv
from hdbcli import dbapi

load_dotenv()
conn = dbapi.connect(
    address=os.getenv("HANA_HOST"),
    port=int(os.getenv("HANA_PORT")),
    user=os.getenv("HANA_USER"),
    password=os.getenv("HANA_PASSWORD"),
    currentSchema="IAL01_DEV",
)
cur = conn.cursor()
text_types = ("NVARCHAR", "VARCHAR", "NCLOB", "CLOB", "SHORTTEXT", "ALPHANUM")

for table in ("@BOY_40_CONFIG", "@BOY_40_CONFIGLINES"):
    cur.execute(
        "SELECT COLUMN_NAME, DATA_TYPE_NAME FROM SYS.TABLE_COLUMNS "
        "WHERE SCHEMA_NAME = 'IAL01_DEV' AND TABLE_NAME = ? ORDER BY POSITION", (table,))
    cols = cur.fetchall()
    text_cols = [c for c, t in cols if t in text_types]
    print("=" * 60)
    print(table, "- text columns:", text_cols)
    where = " OR ".join(f'"{c}" LIKE ? OR "{c}" LIKE ?' for c in text_cols)
    params = []
    for _ in text_cols:
        params += ["%SD017%", "%Truck%"]
    try:
        cur.execute(f'SELECT * FROM "{table}" WHERE {where}', params)
        names = [d[0] for d in cur.description]
        rows = cur.fetchall()
        print("Matching rows:", len(rows))
        for row in rows[:5]:
            print("-" * 40)
            for n, v in zip(names, row):
                if n in [c for c in text_cols] and v not in (None, ""):
                    print(" ", n, "=", str(v)[:700])
    except Exception as e:
        print("Query failed:", e)
conn.close()
