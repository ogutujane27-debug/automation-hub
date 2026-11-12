import os
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings()

url = os.getenv("SL_BASE_URL")
s = requests.Session()
s.verify = False
r = s.post(url + "/Login", json={
    "CompanyDB": os.getenv("SL_COMPANY_DB"),
    "UserName": os.getenv("SL_USER"),
    "Password": os.getenv("SL_PASSWORD"),
}, timeout=30)
print("Login:", r.status_code, "" if r.ok else r.text[:300])
if r.ok:
    r = s.get(url + "/DeliveryNotes?$top=1&$select=DocEntry,DocNum,U_Attachment,AttachmentEntry", timeout=30)
    print("Read:", r.status_code, "ok" if r.ok else r.text[:300])
    s.post(url + "/Logout", timeout=30)
