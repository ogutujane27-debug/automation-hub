from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class RecurringInvoiceTemplate(models.Model):
    ENTITY_CHOICES = [
        ('IAL', 'Ideal Appliances Limited'),
        ('AZL', 'AZL'),
    ]

    entity = models.CharField(max_length=10, choices=ENTITY_CHOICES)
    category = models.CharField(max_length=50, default='Rent')
    expense_name = models.CharField(max_length=255)  # e.g., "Office Rent - Mombasa"
    vendor_name = models.CharField(max_length=255)
    vendor_code = models.CharField(max_length=50, blank=True)  # SAP CardCode
    gl_account = models.CharField(max_length=50, blank=True)   # SAP expense account
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_is_variable = models.BooleanField(default=False)
    cost_center = models.CharField(max_length=100)
    due_day_of_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    is_active = models.BooleanField(default=True)
    last_generated = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.entity}] {self.expense_name} - KSh {self.amount}"

class GeneratedInvoiceLog(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Created', 'Created in SAP'),
        ('Failed', 'Failed'),
    ]

    template = models.ForeignKey(
        RecurringInvoiceTemplate, on_delete=models.PROTECT, related_name='logs'
    )
    period = models.DateField()  # first day of the month being invoiced
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    sap_doc_entry = models.IntegerField(null=True, blank=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(blank=True)
    generated_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['template', 'period'],
                name='one_invoice_per_template_per_month',
            )
        ]

    def __str__(self):
        return f"{self.template} {self.period:%Y-%m} ({self.status})"


from django.conf import settings


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name='+',
    )
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=50)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError('Audit records cannot be changed.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('Audit records cannot be deleted.')

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.username} {self.action} {self.object_repr}"


class EmailLog(models.Model):
    STATUS_CHOICES = [('Sent', 'Sent'), ('Failed', 'Failed')]

    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    to_address = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    kind = models.CharField(max_length=50, blank=True)  # e.g. approval_request, failure_alert, report
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    related_log_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.attempted_at:%Y-%m-%d %H:%M} {self.status} -> {self.to_address}: {self.subject}"
