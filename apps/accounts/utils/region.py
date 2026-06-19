"""Нормализация региона витрины (Москва / СПб) для query-параметров API."""

from apps.accounts.models import District

_VALID = frozenset({District.Region.MOSCOW, District.Region.SAINT_PETERSBURG})

_ALIASES = {
    'moscow': District.Region.MOSCOW,
    'msk': District.Region.MOSCOW,
    'saint_petersburg': District.Region.SAINT_PETERSBURG,
    'saint-petersburg': District.Region.SAINT_PETERSBURG,
    'saintpetersburg': District.Region.SAINT_PETERSBURG,
    'spb': District.Region.SAINT_PETERSBURG,
    'st_petersburg': District.Region.SAINT_PETERSBURG,
    'st-petersburg': District.Region.SAINT_PETERSBURG,
    'petersburg': District.Region.SAINT_PETERSBURG,
}


def normalize_listing_region(value: str | None) -> str | None:
    """Приводит slug/query к `moscow` или `saint_petersburg`."""
    if value is None:
        return None
    raw = (value or '').strip().lower()
    if not raw:
        return None
    if raw in _VALID:
        return raw
    compact = raw.replace('-', '_')
    if compact in _VALID:
        return compact
    return _ALIASES.get(raw) or _ALIASES.get(compact)
