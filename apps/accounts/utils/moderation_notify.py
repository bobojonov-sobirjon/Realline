import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse

logger = logging.getLogger(__name__)


def _moderation_recipients() -> list[str]:
    emails = [x for x in getattr(settings, 'MODERATION_NOTIFY_EMAILS', ()) if x]
    emails.extend(addr for _, addr in getattr(settings, 'ADMINS', ()) if addr)
    seen: set[str] = set()
    out: list[str] = []
    for e in emails:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def send_new_listing_moderation_email(listing_pk: int) -> None:
    """Send email after an agent creates a listing via API (cabinet)."""
    from apps.accounts.models import PropertyListing

    try:
        listing = PropertyListing.objects.select_related('agent').get(pk=listing_pk)
    except PropertyListing.DoesNotExist:
        logger.warning('Moderation email: PropertyListing pk=%s not found', listing_pk)
        return
    if listing.status != PropertyListing.Status.MODERATION:
        return
    recipients = _moderation_recipients()
    if not recipients:
        logger.info(
            'Moderation email skipped (no recipients). Set MODERATION_NOTIFY_EMAILS or ADMINS in settings / .env.'
        )
        return
    base = (getattr(settings, 'PUBLIC_BASE_URL', '') or '').rstrip('/')
    path = reverse('admin:accounts_propertylisting_change', args=[listing.pk])
    admin_url = f'{base}{path}' if base else path
    agent = listing.agent
    agent_label = getattr(agent, 'email', None) or getattr(agent, 'username', '') or str(agent.pk)
    subject = f'[Realline] На модерации: {listing.code} — {listing.name}'
    body = (
        'Агент создал объект через API (личный кабинет).\n\n'
        f'Код: {listing.code}\n'
        f'Название: {listing.name}\n'
        f'Агент: {agent_label}\n'
        f'Цена: {listing.price}\n\n'
        f'Открыть карточку в админке:\n{admin_url}\n'
    )
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception('Moderation notify email failed for listing pk=%s', listing_pk)


def schedule_new_listing_moderation_email(listing_pk: int) -> None:
    """After successful HTTP response / commit — avoid email if transaction rolls back."""
    transaction.on_commit(lambda pk=listing_pk: send_new_listing_moderation_email(pk))
