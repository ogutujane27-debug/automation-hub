from rest_framework import serializers
from .models import RecurringInvoiceTemplate, GeneratedInvoiceLog

class RecurringInvoiceTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringInvoiceTemplate
        fields = '__all__'

class GeneratedInvoiceLogSerializer(serializers.ModelSerializer):
    expense_name = serializers.CharField(source='template.expense_name', read_only=True)
    vendor_name = serializers.CharField(source='template.vendor_name', read_only=True)
    entity = serializers.CharField(source='template.entity', read_only=True)

    class Meta:
        model = GeneratedInvoiceLog
        fields = '__all__'

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
