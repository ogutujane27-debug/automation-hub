import os
import requests
import urllib3


# ============================================================
# SERVICE LAYER - TEST U_Attachment FIELD
# READ-ONLY TEST
# ============================================================

base_url = os.environ.get("SL_BASE_URL", "").rstrip("/")

payload = {
    "CompanyDB": os.environ.get("SL_COMPANY_DB", ""),
    "UserName": os.environ.get("SL_USER", ""),
    "Password": os.environ.get("SL_PASSWORD", ""),
}

missing = []

for name, value in [
    ("SL_BASE_URL", base_url),
    ("SL_COMPANY_DB", payload["CompanyDB"]),
    ("SL_USER", payload["UserName"]),
    ("SL_PASSWORD", payload["Password"]),
]:
    if not value:
        missing.append(name)

if missing:
    print("ERROR: Missing environment variables:")

    for name in missing:
        print(f"  - {name}")

    raise SystemExit(1)


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

session = requests.Session()

session.headers.update({
    "Accept": "application/json",
})


try:

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    print("=" * 70)
    print("SERVICE LAYER - U_Attachment TEST")
    print("=" * 70)
    print()

    print("Logging into Service Layer...")

    login = session.post(
        base_url + "/Login",
        json=payload,
        verify=False,
        timeout=30,
    )

    print("Login HTTP Status:", login.status_code)

    if login.status_code != 200:
        print("LOGIN FAILED")
        print(login.text[:1000])
        raise SystemExit(1)

    print("LOGIN: SUCCESS")
    print()


    # --------------------------------------------------------
    # TEST KNOWN DELIVERY
    # --------------------------------------------------------

    doc_num = "21100978"

    print("Testing delivery number:", doc_num)
    print()

    url = (
        base_url
        + "/DeliveryNotes"
        + f"?$filter=DocNum eq {doc_num}"
        + "&$select=DocEntry,DocNum,CardName,U_Attachment"
    )

    response = session.get(
        url,
        verify=False,
        timeout=30,
    )

    print("HTTP Status:", response.status_code)
    print()

    if response.status_code != 200:
        print("QUERY FAILED")
        print(response.text[:2000])
        raise SystemExit(1)


    # --------------------------------------------------------
    # DISPLAY RESPONSE
    # --------------------------------------------------------

    data = response.json()

    records = data.get("value", [])

    print("Records returned:", len(records))
    print()

    if not records:
        print("No DeliveryNote returned.")
    else:

        print("-" * 70)
        print("SAP RESPONSE")
        print("-" * 70)

        for record in records:

            print("DocEntry:", record.get("DocEntry"))
            print("DocNum:", record.get("DocNum"))
            print("CardName:", record.get("CardName"))

            if "U_Attachment" in record:
                print(
                    "U_Attachment:",
                    repr(record.get("U_Attachment"))
                )
                print()
                print("RESULT: U_Attachment IS EXPOSED")
            else:
                print()
                print("RESULT: U_Attachment IS NOT EXPOSED")

            print()


finally:

    try:

        session.post(
            base_url + "/Logout",
            verify=False,
            timeout=15,
        )

        print("Logged out.")

    except Exception:
        pass