import os
import requests

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
        print(login.text[:500])
        raise SystemExit(1)

    print("LOGIN: SUCCESS")

    response = session.get(
        base_url + "/DeliveryNotes?$top=1",
        verify=False,
        timeout=15
    )

    print("Delivery Notes HTTP Status:", response.status_code)

    if response.status_code == 200:
        print("DELIVERY NOTES READ: SUCCESS")
        print("Response received from SAP.")
    else:
        print("DELIVERY NOTES READ: FAILED")
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
