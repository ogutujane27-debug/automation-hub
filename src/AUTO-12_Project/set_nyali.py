import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')
django.setup()
from django.contrib.auth import get_user_model
from recurring_invoices.models import RecurringInvoiceTemplate, AuditLog

t = RecurringInvoiceTemplate.objects.get(id=15)
new = {
    'category': 'Internet',
    'vendor_name': 'JAMII TELECOMMUNICATIONS LTD',
    'vendor_code': 'SL000196',
    'gl_account': '_SYS00000000707',
    'cost_center': '1571',
}
changes = {}
for k, v in new.items():
    old = str(getattr(t, k))
    if old != v:
        changes[k] = [old, v]
        setattr(t, k, v)
t.save()
user = get_user_model().objects.filter(username='Ogutujane').first()
AuditLog.objects.create(
    user=user, username='Ogutujane', action='edited',
    object_type='RecurringInvoiceTemplate', object_id=str(t.id),
    object_repr=str(t)[:255], changes={**changes, 'via': 'script set_nyali.py'},
)
print("Updated rule", t.id, "->", changes)
