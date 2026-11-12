"""
SERVICE LAYER ATTACHMENTS TEST — READ ONLY

Tests:
1. Service Layer login
2. GET /Attachments2
3. Logout

This test does NOT upload anything.
It does NOT modify SAP.
"""

from pathlib import Path
import sys

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================
# SERVICE LAYER
# ============================================================

import requests

from app.attach_to_sap_service_layer import (
    get_service_layer_session,
    logout_service_layer,
    SL_BASE_URL,
)

requests.packages.urllib3.disable_warnings()

# ============================================================
# TEST
# ============================================================

print("=" * 70)
print("SERVICE LAYER ATTACHMENTS TEST — READ ONLY")
print("=" * 70)
print(f"URL: {SL_BASE_URL}")
print()

session = get_service_layer_session()

if not session:
    print("LOGIN: FAILED")
    sys.exit(1)

print("LOGIN: SUCCESS")
print()

try:
    url = f"{SL_BASE_URL}/Attachments2"

    print("GET /Attachments2")
    print("-" * 70)

    response = requests.get(
        url,
        cookies=session,
        verify=False,
        timeout=30,
    )

    print(f"HTTP Status: {response.status_code}")
    print()

    print("Response:")
    print(response.text[:5000])

    print()

    if response.status_code == 200:
        print("ATTACHMENTS2: ACCESS SUCCESS")
    else:
        print("ATTACHMENTS2: REQUEST FAILED")

finally:
    logout_service_layer(session)
    print()
    print("LOGOUT: COMPLETE")

print()
print("=" * 70)
print("TEST COMPLETE — READ ONLY")
print("=" * 70)