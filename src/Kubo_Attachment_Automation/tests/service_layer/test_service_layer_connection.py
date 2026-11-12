"""
SERVICE LAYER CONNECTIVITY TEST — read-only.

Tests ONLY:
1. Login
2. One DocNum -> DocEntry lookup
3. Logout

Never calls upload_attachment() or link_attachment_to_delivery().
Nothing is written to SAP by this script.

Usage:
    python test_service_layer_connection.py 24215997
"""

from pathlib import Path
import sys

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================
# SERVICE LAYER MODULE
# ============================================================

from app.attach_to_sap_service_layer import (
    get_service_layer_session,
    get_doc_entry_by_docnum,
    logout_service_layer,
    SL_BASE_URL,
    SL_COMPANY_DB,
)

# ============================================================
# ARGUMENT
# ============================================================

if len(sys.argv) != 2:
    print("Usage: python test_service_layer_connection.py <DocNum>")
    sys.exit(1)

test_doc_num = sys.argv[1]

# ============================================================
# TEST
# ============================================================

print("=" * 60)
print("SERVICE LAYER CONNECTIVITY TEST (read-only)")
print("=" * 60)
print(f"URL     : {SL_BASE_URL}")
print(f"Company : {SL_COMPANY_DB}")
print(f"DocNum  : {test_doc_num}")
print()

session = get_service_layer_session()

if not session:
    print("LOGIN: FAILED")
    sys.exit(1)

print("LOGIN: SUCCESS")
print()

try:
    doc_entry = get_doc_entry_by_docnum(
        session,
        test_doc_num
    )

    if doc_entry is not None:
        print(f"DocNum -> DocEntry: SUCCESS")
        print(f"DocNum   : {test_doc_num}")
        print(f"DocEntry : {doc_entry}")
    else:
        print("DocNum -> DocEntry: NOT FOUND")

finally:
    logout_service_layer(session)
    print()
    print("LOGOUT: COMPLETE")

print("=" * 60)
print("TEST COMPLETE — READ ONLY")
print("=" * 60)