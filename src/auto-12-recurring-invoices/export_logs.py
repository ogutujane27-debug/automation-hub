import os, sys, csv, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from recurring_invoices.models import GeneratedInvoiceLog

with open('invoice_log.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Entity', 'Expense', 'Vendor', 'Period', 'Amount', 'Status', 'Invoice No', 'SAP DocEntry', 'Generated'])
    for l in GeneratedInvoiceLog.objects.select_related('template').order_by('-generated_date'):
        t = l.template
        w.writerow([t.entity, t.expense_name, t.vendor_name, l.period, l.amount, l.status, l.invoice_number or '', l.sap_doc_entry or '', l.generated_date])
print("Saved invoice_log.csv")
