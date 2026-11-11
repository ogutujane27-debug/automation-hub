import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from sap_client import SAPServiceLayerClient

def shown(d, skip=()):
    return {k: v for k, v in d.items() if v not in (None, '', 0, 0.0, [], {}) and k not in skip and not k.startswith('odata')}

c = SAPServiceLayerClient()
if not c.login():
    print("SAP login failed."); sys.exit(1)
try:
    print("== Cost centers ==")
    for code in ('1571', '0001'):
        r = c.get(f"ProfitCenters('{code}')")
        print(code, shown(r.json(), ('UserSignature',)) if r.status_code == 200 else r.text[:150])

    print("\n== Latest Jamii A/P invoices (SL000196) ==")
    r = c.get("PurchaseInvoices?$filter=CardCode eq 'SL000196'&$orderby=DocEntry desc&$top=2")
    for d in r.json().get('value', []):
        print("\nDOC:", shown(d, ('DocumentLines', 'TaxExtension', 'AddressExtension', 'DocumentReferences', 'WithholdingTaxDataCollection')))
        for ln in d.get('DocumentLines', [])[:2]:
            print("  LINE:", shown(ln))
finally:
    c.logout()
