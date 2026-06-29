"""Нормализация региона витрины (Москва / СПб) для query-параметров API."""

from apps.accounts.models import District

_VALID = frozenset({District.Region.MOSCOW, District.Region.SAINT_PETERSBURG})

_ALIASES = {
    'moscow': District.Region.MOSCOW,
    'msk': District.Region.MOSCOW,
    'мск': District.Region.MOSCOW,
    'москва': District.Region.MOSCOW,
    'saint_petersburg': District.Region.SAINT_PETERSBURG,
    'saint-petersburg': District.Region.SAINT_PETERSBURG,
    'saintpetersburg': District.Region.SAINT_PETERSBURG,
    'spb': District.Region.SAINT_PETERSBURG,
    'спб': District.Region.SAINT_PETERSBURG,
    'st_petersburg': District.Region.SAINT_PETERSBURG,
    'st-petersburg': District.Region.SAINT_PETERSBURG,
    'petersburg': District.Region.SAINT_PETERSBURG,
    'санкт-петербург': District.Region.SAINT_PETERSBURG,
    'санкт петербург': District.Region.SAINT_PETERSBURG,
    'петербург': District.Region.SAINT_PETERSBURG,
}

# Подписи папок в docs/ (скриншоты для парсера) → код региона витрины.
_FOLDER_ALIASES = {
    'это по спб': District.Region.SAINT_PETERSBURG,
    'это мск': District.Region.MOSCOW,
    'новостройкам мск': District.Region.MOSCOW,
}


def normalize_listing_region(value: str | None) -> str | None:
    """Приводит slug/query/папку к `moscow` или `saint_petersburg`."""
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
    folder_hit = _FOLDER_ALIASES.get(raw)
    if folder_hit:
        return folder_hit
    return _ALIASES.get(raw) or _ALIASES.get(compact)
