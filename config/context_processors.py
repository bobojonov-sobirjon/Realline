"""Template context processors (see TEMPLATES['OPTIONS']['context_processors'])."""


def admin_moderation_pending(request):
    """
    For /admin/ pages: count of listings awaiting review (yellow banner in base_site).
    Skips DB work for non-staff and non-admin URLs.
    """
    path = getattr(request, 'path', '') or ''
    if not path.startswith('/admin/'):
        return {}
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}
    from apps.accounts.models import PropertyListing

    n = PropertyListing.objects.filter(status=PropertyListing.Status.MODERATION).count()
    return {'admin_moderation_pending_count': n}
