from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import RecurringInvoiceTemplate


class DeleteRulesTest(APITestCase):
    def setUp(self):
        self.t = RecurringInvoiceTemplate.objects.create(
            entity='AZL', expense_name='Test', vendor_name='V',
            amount=100, cost_center='CC', due_day_of_month=5)
        self.url = reverse('recurringinvoicetemplate-detail', args=[self.t.id])

    def user_in(self, group):
        u = User.objects.create_user(group.lower(), password='x')
        u.groups.add(Group.objects.get_or_create(name=group)[0])
        return u

    def test_viewer_cannot_delete(self):
        self.client.force_authenticate(self.user_in('Viewer'))
        self.assertEqual(self.client.delete(self.url).status_code, 403)

    def test_preparer_cannot_delete(self):
        self.client.force_authenticate(self.user_in('Preparer'))
        self.assertEqual(self.client.delete(self.url).status_code, 403)

    def test_admin_can_delete(self):
        self.client.force_authenticate(self.user_in('Admin'))
        self.assertEqual(self.client.delete(self.url, {'password': 'x'}, format='json').status_code, 204)

    def test_admin_wrong_password_refused(self):
        self.client.force_authenticate(self.user_in('Admin'))
        self.assertEqual(self.client.delete(self.url, {'password': 'nope'}, format='json').status_code, 403)
        self.assertTrue(RecurringInvoiceTemplate.objects.filter(id=self.t.id).exists())


    def test_admin_can_delete_rule_with_pending_invoice(self):
        from datetime import date
        from .models import GeneratedInvoiceLog
        GeneratedInvoiceLog.objects.create(template=self.t, period=date(2026, 11, 1), amount=100, status='Pending')
        self.client.force_authenticate(self.user_in('Admin'))
        self.assertEqual(self.client.delete(self.url, {'password': 'x'}, format='json').status_code, 204)

    def test_cancel_pending_invoice_needs_password(self):
        from datetime import date
        from .models import GeneratedInvoiceLog
        log = GeneratedInvoiceLog.objects.create(template=self.t, period=date(2026, 11, 1), amount=100, status='Pending')
        url = reverse('generatedinvoicelog-cancel', args=[log.id])
        self.client.force_authenticate(self.user_in('Admin'))
        self.assertEqual(self.client.post(url, {'password': 'nope'}, format='json').status_code, 403)
        self.assertEqual(self.client.post(url, {'password': 'x'}, format='json').status_code, 204)

    def _pending_log(self):
        from datetime import date
        from .models import GeneratedInvoiceLog
        return GeneratedInvoiceLog.objects.create(template=self.t, period=date(2026, 11, 1), amount=100, status='Pending')

    def test_preparer_cannot_approve(self):
        log = self._pending_log()
        self.client.force_authenticate(self.user_in('Preparer'))
        url = reverse('generatedinvoicelog-approve', args=[log.id])
        self.assertEqual(self.client.post(url, {'password': 'x'}, format='json').status_code, 403)
        log.refresh_from_db()
        self.assertEqual(log.status, 'Pending')

    def test_approve_needs_right_password(self):
        log = self._pending_log()
        self.client.force_authenticate(self.user_in('Admin'))
        url = reverse('generatedinvoicelog-approve', args=[log.id])
        self.assertEqual(self.client.post(url, {'password': 'nope'}, format='json').status_code, 403)
        log.refresh_from_db()
        self.assertEqual(log.status, 'Pending')
        self.assertEqual(self.client.post(url, {'password': 'x'}, format='json').status_code, 200)
        log.refresh_from_db()
        self.assertEqual(log.status, 'Approved')
        self.assertEqual(self.client.post(url, {'password': 'x'}, format='json').status_code, 409)
