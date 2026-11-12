from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .audit import record
from .models import RecurringInvoiceTemplate, GeneratedInvoiceLog, AuditLog
from .permissions import RolePermission, AdminOnly
from .serializers import (
    RecurringInvoiceTemplateSerializer, GeneratedInvoiceLogSerializer, AuditLogSerializer,
)

TRACKED = [
    'entity', 'category', 'expense_name', 'vendor_name', 'vendor_code', 'gl_account', 'amount',
    'amount_is_variable', 'cost_center', 'due_day_of_month', 'is_active',
]


def snapshot(obj):
    return {f: str(getattr(obj, f)) for f in TRACKED}


class RecurringInvoiceTemplateViewSet(viewsets.ModelViewSet):
    queryset = RecurringInvoiceTemplate.objects.all().order_by('-created_at')
    serializer_class = RecurringInvoiceTemplateSerializer
    permission_classes = [RolePermission]

    def perform_create(self, serializer):
        obj = serializer.save()
        record(self.request, 'created', obj, {k: [None, v] for k, v in snapshot(obj).items()})

    def perform_update(self, serializer):
        before = snapshot(serializer.instance)
        obj = serializer.save()
        after = snapshot(obj)
        changes = {k: [before[k], after[k]] for k in TRACKED if before[k] != after[k]}
        if changes:
            record(self.request, 'edited', obj, changes)

    def destroy(self, request, *args, **kwargs):
        template = self.get_object()
        password = request.data.get('password', '')
        if not request.user.check_password(password):
            record(request, 'delete_denied', template, {'reason': 'wrong password'})
            return Response(
                {'error': 'Wrong password. Nothing was deleted.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        related = list(template.logs.all())
        if any(l.status == 'Created' for l in related):
            record(request, 'delete_blocked', template, {'reason': 'invoice already created in SAP'})
            return Response(
                {'error': 'An invoice for this rule was already created in SAP, so it cannot be deleted. Pause it instead.'},
                status=status.HTTP_409_CONFLICT,
            )
        details = {
            'snapshot': snapshot(template),
            'logs_deleted': [
                {'period': str(l.period), 'amount': str(l.amount), 'status': l.status} for l in related
            ],
        }
        with transaction.atomic():
            record(request, 'deleted', template, details)
            template.logs.all().delete()
            template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """Queue this month's invoice for a template. Nothing is sent to SAP yet."""
        template = self.get_object()
        if not template.is_active:
            return Response(
                {'error': 'Cannot trigger an inactive invoice template.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.localdate()
        period = today.replace(day=1)

        try:
            with transaction.atomic():
                log = GeneratedInvoiceLog.objects.create(
                    template=template,
                    period=period,
                    amount=template.amount,
                    status='Pending',
                )
        except IntegrityError:
            return Response(
                {'error': f'An invoice for {period:%B %Y} already exists for this template.'},
                status=status.HTTP_409_CONFLICT,
            )

        template.last_generated = today
        template.save(update_fields=['last_generated'])
        record(request, 'triggered', template,
               {'period': str(period), 'amount': str(log.amount), 'log_id': log.id})
        return Response(GeneratedInvoiceLogSerializer(log).data, status=status.HTTP_201_CREATED)


class GeneratedInvoiceLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GeneratedInvoiceLog.objects.all().order_by('-generated_date')
    serializer_class = GeneratedInvoiceLogSerializer
    permission_classes = [RolePermission]

    @action(detail=True, methods=['post'], permission_classes=[AdminOnly])
    def approve(self, request, pk=None):
        """Admin approves a Pending invoice (password required). Nothing is sent to SAP here."""
        log = self.get_object()
        if not request.user.check_password(request.data.get('password', '')):
            record(request, 'approve_denied', log, {'reason': 'wrong password'})
            return Response({'error': 'Wrong password. Nothing was approved.'}, status=status.HTTP_403_FORBIDDEN)
        if log.status != 'Pending':
            record(request, 'approve_blocked', log, {'reason': 'status is ' + log.status})
            return Response({'error': 'Only Pending invoices can be approved.'}, status=status.HTTP_409_CONFLICT)
        with transaction.atomic():
            log.status = 'Approved'
            log.save(update_fields=['status'])
            record(request, 'invoice_approved', log, {'status': ['Pending', 'Approved'], 'amount': str(log.amount), 'period': str(log.period), 'log_id': log.id})
        return Response({'id': log.id, 'status': log.status})
    @action(detail=True, methods=['post'], permission_classes=[AdminOnly])
    def cancel(self, request, pk=None):
        """Admin cancels a Pending invoice (password required). The audit trail keeps the record."""
        log = self.get_object()
        if not request.user.check_password(request.data.get('password', '')):
            record(request, 'cancel_denied', log, {'reason': 'wrong password'})
            return Response({'error': 'Wrong password. Nothing was cancelled.'}, status=status.HTTP_403_FORBIDDEN)
        if log.status not in ('Pending', 'Failed'):
            record(request, 'cancel_blocked', log, {'reason': 'status is ' + log.status})
            return Response({'error': 'Only Pending or Failed invoices can be cancelled.'}, status=status.HTTP_409_CONFLICT)
        details = {'period': str(log.period), 'amount': str(log.amount), 'status': log.status, 'log_id': log.id}
        with transaction.atomic():
            record(request, 'invoice_cancelled', log, details)
            log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [AdminOnly]
