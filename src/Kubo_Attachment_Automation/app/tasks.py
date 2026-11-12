import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SL_BASE_URL = os.environ.get("SL_BASE_URL")
SL_COMPANY_DB = os.environ.get("SL_COMPANY_DB")
SL_USER = os.environ.get("SL_USER")
SL_PASSWORD = os.environ.get("SL_PASSWORD")


def get_sap_session():
    if not all([SL_BASE_URL, SL_COMPANY_DB, SL_USER, SL_PASSWORD]):
        raise RuntimeError(
            "Missing Service Layer environment variables."
        )

    response = requests.post(
        f"{SL_BASE_URL}/Login",
        json={
            "CompanyDB": SL_COMPANY_DB,
            "UserName": SL_USER,
            "Password": SL_PASSWORD,
        },
        verify=False,
        timeout=20,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"SAP Service Layer login failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()["SessionId"]


def get_delivery_entry(session_id, doc_num):
    headers = {
        "Cookie": f"B1SESSION={session_id}"
    }

    url = (
        f"{SL_BASE_URL}/DeliveryNotes"
        f"?%24filter=DocNum%20eq%20{doc_num}"
        f"&%24select=DocEntry,DocNum,CardName"
    )

    response = requests.get(
        url,
        headers=headers,
        verify=False,
        timeout=20,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Delivery lookup failed for {doc_num}: "
            f"{response.status_code} {response.text}"
        )

    records = response.json().get("value", [])

    if not records:
        return None

    return records[0]


def check_attachment_endpoint(session_id):
    headers = {
        "Cookie": f"B1SESSION={session_id}"
    }

    response = requests.get(
        f"{SL_BASE_URL}/Attachments2?%24top=1",
        headers=headers,
        verify=False,
        timeout=20,
    )

    print(f"Attachments2 GET: HTTP {response.status_code}")

    if response.status_code != 200:
        print(response.text)

    return response.status_code == 200


def main():
    print("=" * 60)
    print("KUBO → SAP SERVICE LAYER TEST")
    print("=" * 60)

    print(f"Service Layer: {SL_BASE_URL}")
    print(f"Company DB:    {SL_COMPANY_DB}")
    print(f"SAP user:      {SL_USER}")
    print(
        f"Password set:  "
        f"{'YES' if SL_PASSWORD else 'NO'}"
    )

    session_id = get_sap_session()

    print("[OK] SAP Service Layer login successful.")

    check_attachment_endpoint(session_id)

    doc_num = "26100708"

    delivery = get_delivery_entry(
        session_id,
        doc_num
    )

    if delivery:
        print(
            f"[OK] Delivery found: "
            f"DocNum={delivery['DocNum']} "
            f"DocEntry={delivery['DocEntry']}"
        )
    else:
        print(
            f"[INFO] DocNum {doc_num} was not found "
            f"in {SL_COMPANY_DB}."
        )

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()