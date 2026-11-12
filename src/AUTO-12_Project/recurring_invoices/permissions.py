from rest_framework.permissions import BasePermission, SAFE_METHODS


def role_of(user):
    if user.is_superuser:
        return 'Admin'
    for name in ('Admin', 'Preparer', 'Viewer'):
        if user.groups.filter(name=name).exists():
            return name
    return None


class RolePermission(BasePermission):
    """Viewer: read. Preparer: read/add/edit/trigger. Admin: everything, incl. delete."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = role_of(user)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        if request.method == 'DELETE':
            return role == 'Admin'
        return role in ('Admin', 'Preparer')


class AdminOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and role_of(user) == 'Admin')
