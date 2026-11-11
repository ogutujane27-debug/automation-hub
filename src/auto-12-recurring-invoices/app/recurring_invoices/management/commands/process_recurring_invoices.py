from django.core.management.base import BaseCommand
from django.utils import timezone
from recurring_invoices.models import RecurringInvoiceTemplate, GeneratedInvoiceLog
import uuid

class Command(BaseCommand):
    help = 'Automatically generates recurring monthly invoices due today for IAL & AZL'

    def handle(self, *args, **options):
        today = timezone.now().date()
        current_day = today.day
        
        templates = RecurringInvoiceTemplate.objects.filter(
            is_active=True,
            due_day_of_month=current_day
        )
        
        generated_count = 0
        for template in templates:
            if template.last_generated and template.last_generated.year == today.year and template.last_generated.month == today.month:
                continue
            
            inv_number = f"AUTO-{template.entity}-{today.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
            
            GeneratedInvoiceLog.objects.create(
                template=template,
                invoice_number=inv_number,
                amount=template.amount,
                status='Auto-Generated'
            )
            
            template.last_generated = today
            template.save()
            generated_count += 1
            self.stdout.write(self.style.SUCCESS(f"Generated invoice {inv_number} for {template.expense_name} ({template.entity})"))

        self.stdout.write(self.style.SUCCESS(f"Processed {generated_count} recurring invoices for day {current_day}."))