import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient
c = SAPServiceLayerClient()
if not c.login():
    print("SAP login failed."); sys.exit(1)
try:
    for ep in ('Invoices', 'PurchaseInvoices'):
        r = c.session.get(f"{c.base_url}/{ep}?$select=DocEntry,DocNum,CardCode,DocTotal,CreationDate,Comments&$filter=CreationDate ge '2026-11-09'", verify=False)
        rows = r.json().get('value', []) if r.status_code == 200 else []
        print(f"{ep} created today: {len(rows)}")
        for d in rows:
            print("  ", d)
finally:
    c.logout()
