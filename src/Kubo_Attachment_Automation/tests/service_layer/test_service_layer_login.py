import os
import requests

url = os.environ.get("SL_BASE_URL", "") + "/Login"

payload = {
    "CompanyDB": os.environ.get("SL_COMPANY_DB", ""),
    "UserName": os.environ.get("SL_USER", ""),
    "Password": os.environ.get("SL_PASSWORD", "")
}

try:
    response = requests.post(
        url,
        json=payload,
        verify=False,
        timeout=15
    )

    print("HTTP Status:", response.status_code)

    if response.status_code == 200:
        print("SERVICE LAYER LOGIN: SUCCESS")
    else:
        print("SERVICE LAYER LOGIN: FAILED")
        print("Response:", response.text[:500])

except Exception as e:
    print("CONNECTION ERROR:", str(e))
