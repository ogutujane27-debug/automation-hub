import sys
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.attach_to_sap_service_layer import (
    get_service_layer_session,
    get_doc_entry_by_docnum,
    verify_already_attached,
    copy_pdf_to_sap_share,
    update_u_attachment,
    verify_u_attachment,
    logout_service_layer,
    SL_BASE_URL,
    SL_COMPANY_DB,
)

if len(sys.argv) != 3:
    print('Usage: python controlled_single_attach_test.py <DocNum> <PDF path>')
    sys.exit(1)

doc_num = sys.argv[1]
pdf_path = sys.argv[2]

print('=' * 70)
print('CONTROLLED SINGLE-RECORD ATTACH TEST (PRODUCTION FLOW)')
print('=' * 70)
print(f'Target company : {SL_COMPANY_DB}')
print(f'Service Layer  : {SL_BASE_URL}')
print(f'DocNum         : {doc_num}')
print(f'PDF            : {pdf_path}\n')

session = get_service_layer_session()
if not session:
    print('ABORTED: could not log in to Service Layer.')
    sys.exit(1)
print('[1] Login: SUCCESS')

doc_entry = get_doc_entry_by_docnum(session, doc_num)
if not doc_entry:
    print(f'ABORTED: could not resolve DocEntry for DocNum {doc_num}.')
    logout_service_layer(session)
    sys.exit(1)
print(f'[2] DocEntry resolved: {doc_entry}')

already_attached = verify_already_attached(session, doc_entry)
if already_attached:
    print(f'ABORTED: DocEntry {doc_entry} already has an attachment in SAP.')
    logout_service_layer(session)
    sys.exit(1)
print('[3] Pre-check: no existing attachment safe to proceed')

dest_path = copy_pdf_to_sap_share(pdf_path)
if not dest_path:
    print('ABORTED: copy to SAP share failed. Check logs/attachment_execution.log')
    logout_service_layer(session)
    sys.exit(1)
print(f'[4] PDF copied to SAP share: {dest_path}')

success, err_msg = update_u_attachment(session, doc_entry, dest_path)
if not success:
    print(f'ABORTED: U_Attachment update failed: {err_msg}')
    logout_service_layer(session)
    sys.exit(1)
print('[5] Linked via U_Attachment field: SUCCESS')

confirmed = verify_u_attachment(session, doc_entry, dest_path)
print(f'[6] Post-write verification: present = {confirmed}')

logout_service_layer(session)
print('[7] Logged out.\n')

print('=' * 70)
if confirmed:
    print('TEST SUCCESSFUL - record attached and verified via U_Attachment.')
else:
    print('TEST INCONCLUSIVE - check manually.')
print('=' * 70)
