from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecurringInvoiceTemplateViewSet, GeneratedInvoiceLogViewSet, AuditLogViewSet
from .mail_api import EmailLogViewSet
from .auth_views import login_view, logout_view, me_view

router = DefaultRouter()
router.register(r'recurring-templates', RecurringInvoiceTemplateViewSet)
router.register(r'invoice-logs', GeneratedInvoiceLogViewSet)
router.register(r'audit-log', AuditLogViewSet)
router.register(r'email-log', EmailLogViewSet, basename='email-log')

urlpatterns = [
    path('login/', login_view),
    path('logout/', logout_view),
    path('me/', me_view),
    path('', include(router.urls)),
]
