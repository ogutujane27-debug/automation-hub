import calendar
import os
from urllib.parse import quote

from django.core.management.base import BaseCommand
from django.utils import timezone

from recurring_invoices.models import AuditLog, GeneratedInvoiceLog
from sap_client import SAPServiceLayerClient


def q(value):
    """Escape a value for use inside an OData URL."""
    return quote(str(value).replace("'", "''"), safe='')


def audit(action, log, changes):
    AuditLog.objects.create(
        username='sync_sap_invoices', action=action, object_type='GeneratedInvoiceLog',
        object_id=str(log.id), object_repr=str(log)[:255], changes=changes,
    )


class Command(BaseCommand):
    help = ('Send APPROVED recurring invoices to SAP as purchase invoices. '
            'DRY RUN (sends nothing) unless --execute is given.')

    def add_arguments(self, parser):
        parser.add_argument('--company', default=None, help='SAP company database (default: SAP_COMPANY_DB)')
        parser.add_argument('--execute', action='store_true', help='Really create the invoices in SAP')
        parser.add_argument('--allow-live', action='store_true', help='Needed to execute against a non-DEV company')
        parser.add_argument('--limit', type=int, default=1, help='With --execute: max invoices to send (default 1)')

    def handle(self, *args, **opts):
        execute = opts['execute']
        company = opts['company'] or os.getenv('SAP_COMPANY_DB') or ''
        if execute and 'DEV' not in company.upper() and not opts['allow_live']:
            self.stdout.write(self.style.ERROR(f"Refusing to execute against '{company}' (not a DEV company). Use --allow-live if you really mean it."))
            return

        logs = GeneratedInvoiceLog.objects.filter(status='Approved').select_related('template').order_by('id')
        if execute:
            logs = logs[:opts['limit']]
        logs = list(logs)
        mode = 'EXECUTE' if execute else 'DRY RUN (nothing will be sent)'
        self.stdout.write(self.style.NOTICE(f"{mode} | company: {company} | approved invoices: {len(logs)}"))
        if not logs:
            self.stdout.write("No Approved invoices to process.")
            return

        client = SAPServiceLayerClient(company or None)
        if not client.login():
            self.stdout.write(self.style.ERROR("SAP login failed. Aborting."))
            return

        sent = blocked = 0
        try:
            for log in logs:
                t = log.template
                problems = []
                supplier_name = ''

                if not t.vendor_code:
                    problems.append("rule has no vendor_code")
                else:
                    r = client.get(f"BusinessPartners('{q(t.vendor_code)}')?$select=CardCode,CardName,CardType")
                    if r.status_code != 200:
                        problems.append(f"supplier '{t.vendor_code}' not found in {company}")
                    else:
                        bp = r.json()
                        supplier_name = bp.get('CardName', '')
                        if bp.get('CardType') != 'cSupplier':
                            problems.append(f"'{t.vendor_code}' is not a supplier in SAP")

                if not t.gl_account:
                    problems.append("rule has no GL account")
                elif not client.exists(f"ChartOfAccounts('{q(t.gl_account)}')?$select=Code"):
                    problems.append(f"GL account '{t.gl_account}' not found in {company}")

                if t.cost_center and not client.exists(f"ProfitCenters('{q(t.cost_center)}')?$select=CenterCode"):
                    problems.append(f"cost center '{t.cost_center}' not found in {company}")

                ref = f"AUTO-12-{log.period:%Y-%m}-L{log.id}"
                try:
                    dup = client.get(f"PurchaseInvoices?$select=DocEntry,DocNum&$filter=NumAtCard eq '{q(ref)}'")
                    found = dup.json().get('value', []) if dup.status_code == 200 else []
                except Exception:
                    found = []
                if found:
                    problems.append(f"SAP already has this invoice (DocEntry {found[0].get('DocEntry')})")

                today = timezone.localdate()
                last_day = calendar.monthrange(log.period.year, log.period.month)[1]
                due = log.period.replace(day=min(int(t.due_day_of_month), last_day))
                payload = {
                    "DocType": "dDocument_Service",
                    "CardCode": t.vendor_code,
                    "DocDate": today.isoformat(),
                    "DocDueDate": due.isoformat(),
                    "NumAtCard": ref,
                    "Comments": f"AUTO-12 recurring: {t.expense_name} {log.period:%Y-%m}",
                    "DocumentLines": [{
                        "ItemDescription": t.expense_name,
                        "AccountCode": t.gl_account,
                        "LineTotal": float(log.amount),
                        "CostingCode": t.cost_center,
                    }],
                }

                series = os.getenv('SAP_INVOICE_SERIES', '').strip()
                if series.isdigit():
                    payload["Series"] = int(series)
                else:
                    self.stdout.write(self.style.WARNING("  SAP_INVOICE_SERIES is not set in .env - SAP will refuse the invoice without a numbering series."))
                self.stdout.write(f"\n--- Log {log.id}: [{t.entity}] {t.expense_name} | {log.period:%Y-%m} | KSh {log.amount} ---")
                self.stdout.write(f"  Supplier : {t.vendor_code or '(none)'} {supplier_name}")
                self.stdout.write(f"  GL       : {t.gl_account or '(none)'}   Cost center: {t.cost_center or '(none)'}")
                self.stdout.write(f"  Due      : {due}   Ref: {ref}   (VAT: not set, SAP default applies)")
                if problems:
                    blocked += 1
                    for p in problems:
                        self.stdout.write(self.style.WARNING(f"  BLOCKED: {p}"))
                    if execute:
                        audit('sap_push_blocked', log, {'problems': problems})
                    continue

                self.stdout.write(self.style.SUCCESS("  Ready to send."))
                if not execute:
                    continue

                data, err = client.create_purchase_invoice(payload)
                if data:
                    log.status = 'Created'
                    log.sap_doc_entry = data.get('DocEntry')
                    log.invoice_number = str(data.get('DocNum', ''))
                    log.error_message = ''
                    log.save()
                    t.last_generated = timezone.localdate()
                    t.save(update_fields=['last_generated'])
                    audit('sap_invoice_created', log, {'DocEntry': log.sap_doc_entry, 'DocNum': log.invoice_number, 'company': company})
                    sent += 1
                    self.stdout.write(self.style.SUCCESS(f"  CREATED in SAP: DocEntry {log.sap_doc_entry}, DocNum {log.invoice_number}"))
                else:
                    log.status = 'Failed'
                    log.error_message = err
                    log.save()
                    audit('sap_invoice_failed', log, {'error': err, 'company': company})
                    self.stdout.write(self.style.ERROR(f"  FAILED: {err}"))
        finally:
            client.logout()
        self.stdout.write(f"\nDone. Ready/sent: {len(logs) - blocked}/{sent} | Blocked: {blocked}")
