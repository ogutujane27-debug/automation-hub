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

cur.execute('SELECT * FROM "@TBLVEHICLE" LIMIT 3')
print("Columns:", [d[0] for d in cur.description])
for row in cur.fetchall():
    print("  ", row)
cur.execute('SELECT COUNT(*) FROM "@TBLVEHICLE"')
print("Rows in vehicle table:", cur.fetchone()[0])

trucks = {
    "25101877": "KCX282D", "25110676": "KDJ 141K/1", "25115301": "KDJ 141K/2",
    "25116757": "KDE 065Z/00", "25205409": "SELF COLLECTION/00", "25216146": "KCR 296A/1",
    "25216169": "KCP 651U/1", "25219635": "KCQ 712F", "25221091": "KCX 285D/1",
    "25221401": "KDJ 616N", "25221586": "KCX 285D/1", "25221959": "KCQ 712F/1",
    "25300389": "KCY 018S/1",
}
print()
for doc, t in trucks.items():
    cur.execute('SELECT COUNT(*) FROM "@TBLVEHICLE" WHERE "Code" = ? OR "Name" = ?', (t, t))
    print(doc, "|", t, "->", "FOUND" if cur.fetchone()[0] else "not in table")
conn.close()
