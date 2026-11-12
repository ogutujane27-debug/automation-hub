import os
import csv
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings()

rows = list(csv.DictReader(open("reports/attachment_decision_report.csv", encoding="utf-8-sig")))
todo = [r for r in rows if r["Status"] in ("TO_ATTACH", "REVIEW") and r["SAP_DocNum"]]

url = os.getenv("SL_BASE_URL")
s = requests.Session()
s.verify = False
r = s.post(url + "/Login", json={
    "CompanyDB": os.getenv("SL_COMPANY_DB"),
    "UserName": os.getenv("SL_USER"),
    "Password": os.getenv("SL_PASSWORD"),
}, timeout=30)
r.raise_for_status()

print("DocNum     TruckNo(U_TruckNo)   VehiclePlate")
for t in todo:
    q = f"/DeliveryNotes?$filter=DocNum eq {t['SAP_DocNum']}&$select=DocNum,VehiclePlate,U_TruckNo"
    r = s.get(url + q, timeout=30)
    v = r.json().get("value", [{}])[0] if r.ok else {}
    print(t["SAP_DocNum"], "|", v.get("U_TruckNo"), "|", v.get("VehiclePlate"))

r = s.get(url + "/U_TBLVEHICLE?$top=3", timeout=30)
print("Vehicle table sample:", r.status_code, r.text[:400] if not r.ok else r.json().get("value"))
s.post(url + "/Logout", timeout=30)
