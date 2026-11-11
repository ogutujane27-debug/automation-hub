import os, sys, csv, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient

client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    rows, skip = [], 0
    while skip < 5000:
        r = client.session.get(f"{client.base_url}/BusinessPartners?$select=CardCode,CardName&$filter=CardType eq 'cSupplier'&$orderby=CardCode&$skip={skip}", verify=False)
        batch = r.json().get('value', []) if r.status_code == 200 else []
        if not batch:
            break
        rows += batch
        skip += len(batch)
    with open('sap_suppliers.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['CardCode', 'CardName'])
        for b in rows:
            w.writerow([b['CardCode'], b['CardName']])
    print(f"Saved {len(rows)} suppliers to sap_suppliers.csv")
finally:
    client.logout()
