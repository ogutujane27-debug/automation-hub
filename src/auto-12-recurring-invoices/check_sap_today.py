import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sap_client import SAPServiceLayerClient
c = SAPServiceLayerClient()
if not c.login():
    print("SAP login failed."); sys.exit(1)
try:
    for ep in ('Invoices', 'PurchaseInvoices'):
        r = c.get(f"{ep}?$select=DocEntry,DocNum,CardCode,DocTotal,CreationDate,NumAtCard&$filter=CreationDate ge '2026-11-10'")
        rows = r.json().get('value', []) if r.status_code == 200 else []
        print(f"{ep} created today: {len(rows)}")
        for d in rows:
            print("  ", d)
finally:
    c.logout()
