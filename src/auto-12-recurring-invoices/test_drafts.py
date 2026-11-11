import os, sys, copy, django
from datetime import date
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient
from recurring_invoices.models import RecurringInvoiceTemplate

t = RecurringInvoiceTemplate.objects.get(id=15)
REF = 'AUTO-12-DRAFT-TEST'
base = {
    "DocObjectCode": "oPurchaseInvoices",
    "DocType": "dDocument_Service",
    "CardCode": t.vendor_code,
    "DocDate": date.today().isoformat(),
    "DocDueDate": date(2026, 11, 25).isoformat(),
    "NumAtCard": REF,
    "DocumentLines": [{"ItemDescription": t.expense_name, "AccountCode": t.gl_account,
                       "LineTotal": 73900.0, "CostingCode": t.cost_center}],
}

def with_line(p, **extra):
    q = copy.deepcopy(p)
    q["DocumentLines"][0].update(extra)
    return q

v2 = with_line(base, VatGroup='I1')
v3 = copy.deepcopy(v2); v3["Series"] = 790
v4 = with_line(v3, CostingCode2='0002', CostingCode3='0003', CostingCode4='2447')
variants = [
    ("V1 as the pipeline sends it", base),
    ("V2 + VatGroup I1", v2),
    ("V3 + Series 790", v3),
    ("V4 + dimensions 2, 3, 4", v4),
]

c = SAPServiceLayerClient()
if not c.login():
    print("SAP login failed."); sys.exit(1)
try:
    for name, payload in variants:
        r = c.session.post(f"{c.base_url}/Drafts", json=payload, timeout=30)
        if r.status_code == 201:
            de = r.json().get('DocEntry')
            d = c.session.delete(f"{c.base_url}/Drafts({de})", timeout=20)
            print(f"{name}: ACCEPTED as draft (DocEntry {de}), deleted: {d.status_code in (200, 204)}")
        else:
            try:
                msg = r.json()['error']['message']['value']
            except Exception:
                msg = r.text[:200]
            print(f"{name}: REFUSED [{r.status_code}] {msg}")
    left = c.get(f"Drafts?$filter=NumAtCard eq '{REF}'&$select=DocEntry")
    print("Leftover test drafts:", len(left.json().get('value', [])) if left.status_code == 200 else left.text[:100])
finally:
    c.logout()
