import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient

terms = [a.lower() for a in sys.argv[1:]]
client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    rows, skip = [], 0
    while skip < 3000:
        r = client.session.get(f"{client.base_url}/BusinessPartners?$select=CardCode,CardName,CardType&$filter=CardType eq 'cSupplier'&$orderby=CardCode&$skip={skip}", verify=False)
        batch = r.json().get('value', []) if r.status_code == 200 else []
        if not batch:
            break
        rows += batch
        skip += len(batch)
    print(f"V10001 exists as supplier: {any(b['CardCode'] == 'V10001' for b in rows)}")
    for t in terms:
        print(f"\nMatches for '{t}':")
        for b in rows:
            if t in b['CardName'].lower():
                print(f"  {b['CardCode']} | {b['CardName']}")
finally:
    client.logout()
