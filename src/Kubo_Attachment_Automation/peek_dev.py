import os
import csv
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings()

rows = list(csv.DictReader(open("reports/attachment_decision_report.csv", encoding="utf-8-sig")))
todo = [r for r in rows if r["Status"] == "TO_ATTACH"]
print("TO_ATTACH in report:", len(todo))
for r in todo[:5]:
    print("  ", r["Filename"], r["SAP_DocNum"])

url = os.getenv("SL_BASE_URL")
s = requests.Session()
s.verify = False
r = s.post(url + "/Login", json={
    "CompanyDB": os.getenv("SL_COMPANY_DB"),
    "UserName": os.getenv("SL_USER"),
    "Password": os.getenv("SL_PASSWORD"),
}, timeout=30)
r.raise_for_status()

if todo:
    doc = todo[0]["SAP_DocNum"]
    q = f"/DeliveryNotes?$filter=DocNum eq {doc}&$select=DocEntry,DocNum,DocDate,U_Attachment,AttachmentEntry"
    r = s.get(url + q, timeout=30)
    print("First TO_ATTACH in DEV:", r.status_code, r.json().get("value") if r.ok else r.text[:300])

q = "/DeliveryNotes?$filter=U_Attachment ne null&$top=3&$orderby=DocEntry desc&$select=DocNum,U_Attachment"
r = s.get(url + q, timeout=30)
print("Examples already attached:", r.status_code)
if r.ok:
    for d in r.json().get("value", []):
        print(" ", d["DocNum"], d["U_Attachment"])
else:
    print(r.text[:300])
s.post(url + "/Logout", timeout=30)
