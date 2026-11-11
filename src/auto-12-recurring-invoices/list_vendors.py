import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()

from sap_client import SAPServiceLayerClient

client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    rows, skip = [], 0
    while True:
        url = f"{client.base_url}/BusinessPartners?$select=CardCode,CardName,CardType&$filter=CardType eq 'cSupplier'&$orderby=CardCode&$skip={skip}"
        r = client.session.get(url, verify=False)
        if r.status_code != 200:
            print("SAP error:", r.text[:200]); break
        batch = r.json().get('value', [])
        if not batch:
            break
        rows += batch
        skip += len(batch)
        if skip >= 2000:
            break
    print(f"Suppliers found in SAP: {len(rows)}")
    print("\nFirst 30:")
    for bp in rows[:30]:
        print(f"  {bp['CardCode']} | {bp['CardName']}")
    print("\nContaining 'coast' (any case):")
    for bp in rows:
        if 'coast' in bp['CardName'].lower():
            print(f"  {bp['CardCode']} | {bp['CardName']}")
finally:
    client.logout()
