import os, sys, csv, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient

words = ['rent', 'lease', 'security', 'guard', 'electric', 'water', 'utilit', 'internet', 'telephone', 'power', 'service charge']
client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    accts, skip = [], 0
    while skip < 10000:
        r = client.session.get(f"{client.base_url}/ChartOfAccounts?$select=Code,Name,ActiveAccount&$orderby=Code&$skip={skip}", verify=False)
        batch = r.json().get('value', []) if r.status_code == 200 else []
        if not batch:
            break
        accts += batch
        skip += len(batch)
    with open('gl_candidates.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['GL Account', 'GL Name', 'Active'])
        for a in accts:
            if any(x in a['Name'].lower() for x in words):
                w.writerow([a['Code'], a['Name'], a.get('ActiveAccount')])
    print(f"Chart of accounts: {len(accts)} accounts scanned")
    cc, skip = [], 0
    while skip < 5000:
        r = client.session.get(f"{client.base_url}/ProfitCenters?$select=CenterCode,CenterName,Active&$skip={skip}", verify=False)
        batch = r.json().get('value', []) if r.status_code == 200 else []
        if not batch:
            break
        cc += batch
        skip += len(batch)
    with open('cost_centers.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Cost Center', 'Name', 'Active'])
        for c in cc:
            w.writerow([c['CenterCode'], c['CenterName'], c.get('Active')])
    print(f"Cost centers saved: {len(cc)}")
finally:
    client.logout()
