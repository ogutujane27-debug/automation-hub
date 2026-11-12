import os
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand

from recurring_invoices.models import EmailLog, GeneratedInvoiceLog

try:
    from dotenv import load_dotenv
    load_dotenv(Path(settings.BASE_DIR) / '.env')
except Exception:
    pass


class Command(BaseCommand):
    help = 'Email an alert for each Failed invoice that has not been alerted yet. Every attempt is recorded in EmailLog.'

    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', help='Send one test email to check the mail settings')

    def handle(self, *args, **opts):
        host = os.getenv('SMTP_HOST')
        user = os.getenv('SMTP_USER')
        password = os.getenv('SMTP_PASSWORD')
        port = int(os.getenv('SMTP_PORT', '587'))
        use_ssl = port == 465
        use_tls = (not use_ssl) and os.getenv('SMTP_USE_TLS', 'true').lower() != 'false'
        sender = os.getenv('ALERT_EMAIL_FROM') or user
        to = [a.strip() for a in os.getenv('ALERT_EMAIL_TO', '').split(',') if a.strip()]

        missing = [n for n, v in (('SMTP_HOST', host), ('SMTP_USER', user), ('SMTP_PASSWORD', password), ('ALERT_EMAIL_TO', to)) if not v]
        if missing:
            self.stdout.write(self.style.ERROR('Mail not configured. Missing in .env: ' + ', '.join(missing)))
            return

        conn = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=host, port=port, username=user, password=password,
            use_tls=use_tls, use_ssl=use_ssl, timeout=20,
        )

        jobs = []
        if opts['test']:
            jobs.append(('AUTO-12 test email', 'This is a test email from AUTO-12. If you can read it, mail is configured correctly.', 'test', None))
        else:
            already = set(EmailLog.objects.filter(kind='failure_alert', status='Sent').values_list('related_log_id', flat=True))
            failed = GeneratedInvoiceLog.objects.filter(status='Failed').select_related('template').order_by('id')
            for log in failed:
                if log.id in already:
                    continue
                t = log.template
                subject = f"AUTO-12 ALERT: invoice failed - {t.expense_name} ({t.entity}) {log.period:%Y-%m}"
                body = (
                    f"An invoice failed to post to SAP.\n\n"
                    f"Entity   : {t.entity}\n"
                    f"Expense  : {t.expense_name}\n"
                    f"Vendor   : {t.vendor_name} ({t.vendor_code or 'no code'})\n"
                    f"Period   : {log.period:%Y-%m}\n"
                    f"Amount   : KSh {log.amount}\n"
                    f"Log ID   : {log.id}\n\n"
                    f"Error:\n{log.error_message or '(no message recorded)'}\n"
                )
                jobs.append((subject, body, 'failure_alert', log.id))

        if not jobs:
            self.stdout.write('No new failed invoices to alert on.')
            return

        sent = failed_n = 0
        for subject, body, kind, log_id in jobs:
            try:
                EmailMessage(subject, body, sender, to, connection=conn).send()
                status, err = 'Sent', ''
                sent += 1
            except Exception as e:
                status, err = 'Failed', str(e)[:2000]
                failed_n += 1
            EmailLog.objects.create(
                to_address=', '.join(to)[:255], subject=subject[:255], kind=kind,
                status=status, error_message=err, related_log_id=log_id,
            )
            self.stdout.write((self.style.SUCCESS if status == 'Sent' else self.style.ERROR)(f"{status}: {subject}" + (f" ({err})" if err else '')))
        self.stdout.write(f"Done. Sent: {sent} | Failed: {failed_n}")