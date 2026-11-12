import os, sys, csv, django
from collections import Counter
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient

client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    counts, sample = Counter(), {}
    for skip in range(0, 500, 100):
        r = client.session.get(f"{client.base_url}/PurchaseInvoices?$select=DocEntry,CardCode,DocumentLines&$orderby=DocEntry desc&$top=100&$skip={skip}", verify=False)
        if r.status_code != 200:
            print("SAP error:", r.text[:200]); break
        for d in r.json().get('value', []):
            for ln in d.get('DocumentLines', []):
                key = (ln.get('AccountCode'), ln.get('TaxCode'), ln.get('CostingCode'))
                counts[key] += 1
                sample.setdefault(key, ln.get('ItemDescription'))
    names = {}
    for code in {k[0] for k in counts if k[0]}:
        r = client.session.get(f"{client.base_url}/ChartOfAccounts('{code}')?$select=Code,Name", verify=False)
        names[code] = r.json().get('Name') if r.status_code == 200 else ''
    with open('gl_accounts_used.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Times used', 'GL Account', 'GL Name', 'Tax Code', 'Cost Center', 'Sample description'])
        for (acct, tax, cc), n in counts.most_common():
            w.writerow([n, acct, names.get(acct, ''), tax, cc, sample[(acct, tax, cc)]])
    print(f"Saved {len(counts)} combinations to gl_accounts_used.csv")
finally:
    client.logout()
