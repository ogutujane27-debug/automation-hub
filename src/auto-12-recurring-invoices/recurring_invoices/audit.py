from .models import AuditLog


def record(request, action, obj=None, changes=None, user=None):
    actor = user if user is not None else getattr(request, 'user', None)
    authed = actor is not None and getattr(actor, 'is_authenticated', False)
    AuditLog.objects.create(
        user=actor if authed else None,
        username=actor.username if authed else '',
        action=action,
        object_type=obj.__class__.__name__ if obj is not None else '',
        object_id=str(obj.pk) if obj is not None else '',
        object_repr=str(obj)[:255] if obj is not None else '',
        changes=changes or {},
        ip_address=request.META.get('REMOTE_ADDR'),
    )
