import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()

from sap_client import SAPServiceLayerClient
from recurring_invoices.models import RecurringInvoiceTemplate

client = SAPServiceLayerClient()
if not client.login():
    print("SAP login failed."); sys.exit(1)
try:
    seen = set()
    for t in RecurringInvoiceTemplate.objects.filter(is_active=True):
        key = (t.entity, t.vendor_name)
        if key in seen:
            continue
        seen.add(key)
        word = max(t.vendor_name.split(), key=len)
        url = f"{client.base_url}/BusinessPartners?$select=CardCode,CardName,CardType&$filter=CardType eq 'cSupplier' and contains(CardName,'{word}')"
        r = client.session.get(url, verify=False)
        print(f"\n[{t.entity}] template '{t.expense_name}' vendor '{t.vendor_name}' (searched '{word}')")
        if r.status_code != 200:
            print("  SAP error:", r.text[:200]); continue
        for bp in r.json().get('value', []):
            print(f"  {bp['CardCode']} | {bp['CardName']}")
finally:
    client.logout()
