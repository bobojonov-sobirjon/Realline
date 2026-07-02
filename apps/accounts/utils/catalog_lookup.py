"""Поиск объекта каталога по slug или числовому id."""

from __future__ import annotations

from django.shortcuts import get_object_or_404

from apps.accounts.models import PropertyListing


def resolve_catalog_listing(lookup: str, *, published_only: bool = True) -> PropertyListing:
    """
    Сначала slug (в т.ч. числовой «1733»), затем pk для обратной совместимости.
    """
    lookup = (lookup or '').strip()
    qs = PropertyListing.objects.all()
    if published_only:
        qs = qs.filter(status=PropertyListing.Status.PUBLISHED)

    by_slug = qs.filter(slug=lookup).first()
    if by_slug:
        return by_slug

    if lookup.isdigit():
        return get_object_or_404(qs, pk=int(lookup))

    return get_object_or_404(qs, slug=lookup)
