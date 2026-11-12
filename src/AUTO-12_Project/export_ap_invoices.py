import os, sys, csv, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient

client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    url = f"{client.base_url}/PurchaseInvoices?$orderby=DocEntry desc&$top=50"
    r = client.session.get(url, headers={'Prefer': 'odata.maxpagesize=50'}, verify=False)
    if r.status_code != 200:
        print("SAP error:", r.text[:300]); sys.exit(1)
    docs = r.json().get('value', [])
    with open('sap_ap_invoices.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['DocEntry', 'DocNum', 'CardCode', 'CardName', 'DocDate', 'DueDate', 'DocTotal', 'Currency', 'VendorRef', 'Comments', 'Line GL Account', 'Line Description', 'Line Total', 'Cost Center'])
        for d in docs:
            lines = d.get('DocumentLines') or [{}]
            for ln in lines:
                w.writerow([d.get('DocEntry'), d.get('DocNum'), d.get('CardCode'), d.get('CardName'), d.get('DocDate'), d.get('DocDueDate'), d.get('DocTotal'), d.get('DocCurrency'), d.get('NumAtCard'), d.get('Comments'), ln.get('AccountCode'), ln.get('ItemDescription'), ln.get('LineTotal'), ln.get('CostingCode')])
    print(f"Saved {len(docs)} invoices to sap_ap_invoices.csv")
finally:
    client.logout()
