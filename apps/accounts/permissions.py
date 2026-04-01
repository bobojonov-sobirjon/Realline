from rest_framework.permissions import BasePermission

from apps.accounts.models import PropertyListing


class IsAgentOwner(BasePermission):
    """Доступ только владельцу объекта (агенту)."""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, PropertyListing):
            return obj.agent_id == request.user.pk
        return False
