import os
import requests

BASE_URL = os.getenv("SL_BASE_URL")
COMPANY_DB = os.getenv("SL_COMPANY_DB")
USER = os.getenv("SL_USER")
PASSWORD = os.getenv("SL_PASSWORD")

if not all([BASE_URL, COMPANY_DB, USER, PASSWORD]):
    raise RuntimeError("Missing Service Layer environment variables.")

session = requests.Session()
session.verify = False

login_url = f"{BASE_URL}/Login"

login_payload = {
    "CompanyDB": COMPANY_DB,
    "UserName": USER,
    "Password": PASSWORD,
}

print("Logging in...")

login_response = session.post(
    login_url,
    json=login_payload,
    timeout=30,
)

print(f"Login HTTP status: {login_response.status_code}")

if login_response.status_code != 200:
    print(login_response.text)
    raise SystemExit(1)

print("Login successful.")

# ------------------------------------------------------------
# READ-ONLY TEST
# Existing delivery known to already have an attachment
# ------------------------------------------------------------

doc_num = 21100978

url = (
    f"{BASE_URL}/DeliveryNotes"
    f"?$filter=DocNum%20eq%20{doc_num}"
    f"&$select=DocEntry,DocNum,CardName,AttachmentEntry,U_Attachment"
)

print()
print(f"Reading Delivery Note {doc_num}...")
print(url)

response = session.get(
    url,
    timeout=30,
)

print(f"GET HTTP status: {response.status_code}")

if response.status_code != 200:
    print(response.text)
    raise SystemExit(1)

data = response.json()
records = data.get("value", [])

if not records:
    print("Delivery Note not found.")
else:
    record = records[0]

    print()
    print("DELIVERY NOTE")
    print("------------------------------")
    print(f"DocEntry       : {record.get('DocEntry')}")
    print(f"DocNum         : {record.get('DocNum')}")
    print(f"CardName       : {record.get('CardName')}")
    print(f"AttachmentEntry: {record.get('AttachmentEntry')}")
    print(f"U_Attachment   : {record.get('U_Attachment')}")
    print("------------------------------")

print()
print("Logging out...")

logout_response = session.post(
    f"{BASE_URL}/Logout",
    timeout=30,
)

print(f"Logout HTTP status: {logout_response.status_code}")
print("Test complete. READ-ONLY. No SAP data was changed.")
