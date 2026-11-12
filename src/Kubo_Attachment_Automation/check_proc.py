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
cur.execute(
    "SELECT PROCEDURE_NAME, DEFINITION FROM SYS.PROCEDURES "
    "WHERE SCHEMA_NAME = 'IAL01_DEV' AND UPPER(PROCEDURE_NAME) LIKE '%TRANSACTIONNOTIFICATION%'")
rows = cur.fetchall()
print("Procedures found:", [r[0] for r in rows])

for name, d in rows:
    text = d.read() if hasattr(d, "read") else str(d)
    print("=" * 60)
    print(name, "- length:", len(text))
    i = text.find("SD017")
    if i < 0:
        print("SD017 not found in this procedure")
        continue
    print("SD017 found. Code around it:")
    print("-" * 60)
    print(text[max(0, i - 1800): i + 400])
conn.close()
