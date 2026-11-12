import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient

client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    print("Cost center lookup check (should be True for real codes):")
    for code in ('1', '1570', '1571'):
        print(" ", code, client.exists(f"ProfitCenters('{code}')?$select=CenterCode"))
    print("\nA/P invoices booked to _SYS00000000707 (Email & Internet Expenses):")
    for skip in range(0, 500, 100):
        r = client.get(f"PurchaseInvoices?$select=DocEntry,DocNum,CardCode,CardName,DocDate,DocType,DocumentLines&$orderby=DocEntry desc&$top=100&$skip={skip}")
        if r.status_code != 200:
            print("SAP error:", r.text[:200]); break
        for d in r.json().get('value', []):
            for ln in d.get('DocumentLines', []):
                if ln.get('AccountCode') == '_SYS00000000707':
                    print(f"  DocNum {d['DocNum']} | {d['DocDate']} | {d['CardCode']} | {d['CardName']} | DocType {d.get('DocType')} | line total {ln.get('LineTotal')} | cost center {ln.get('CostingCode')} | {ln.get('ItemDescription')}")
finally:
    client.logout()
