import os
import requests

DOC_NUM = 26101429

base_url = os.environ.get("SL_BASE_URL", "")
login_url = base_url + "/Login"

payload = {
    "CompanyDB": os.environ.get("SL_COMPANY_DB", ""),
    "UserName": os.environ.get("SL_USER", ""),
    "Password": os.environ.get("SL_PASSWORD", "")
}

session = requests.Session()

try:
    login = session.post(
        login_url,
        json=payload,
        verify=False,
        timeout=15
    )

    print("Login HTTP Status:", login.status_code)

    if login.status_code != 200:
        print("LOGIN FAILED")
        raise SystemExit(1)

    print("LOGIN: SUCCESS")

    url = (
        base_url
        + f"/DeliveryNotes?$filter=DocNum eq {DOC_NUM}"
        + "&$select=DocEntry,DocNum,CardName"
    )

    response = session.get(
        url,
        verify=False,
        timeout=15
    )

    print("DocNum lookup HTTP Status:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        results = data.get("value", [])

        if results:
            print("DOCNUM LOOKUP: SUCCESS")
            print("SAP result:", results[0])
        else:
            print("DOCNUM LOOKUP: SUCCESS - no matching Delivery Note found")
    else:
        print("DOCNUM LOOKUP: FAILED")
        print(response.text[:500])

finally:
    try:
        session.post(
            base_url + "/Logout",
            verify=False,
            timeout=15
        )
        print("Logged out.")
    except Exception:
        pass
