import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient
c = SAPServiceLayerClient()
if not c.login():
    print("SAP login failed."); sys.exit(1)
try:
    r = c.get("PurchaseInvoices?$filter=startswith(NumAtCard,'AUTO-12')&$select=DocEntry,DocNum,CardCode,CardName,DocDate,DocDueDate,DocTotal,VatSum,NumAtCard,DocumentLines")
    for d in r.json().get('value', []):
        print({k: v for k, v in d.items() if k != 'DocumentLines'})
        for ln in d.get('DocumentLines', []):
            print("   line:", ln.get('AccountCode'), ln.get('LineTotal'), ln.get('CostingCode'), ln.get('VatGroup'), ln.get('ItemDescription'))
finally:
    c.logout()
