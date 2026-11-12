import os
import sys
import django

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Point directly to your settings module package name
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mika_automation_new.settings')

django.setup()

from recurring_invoices.models import RecurringInvoiceTemplate

templates = RecurringInvoiceTemplate.objects.filter(is_active=True)
print("--- Local Recurring Invoice Templates ---")
for t in templates:
    print(f"ID: {t.id} | Name: {t.expense_name} | Vendor Name: {t.vendor_name} | Current CardCode: {repr(t.vendor_code)}")
