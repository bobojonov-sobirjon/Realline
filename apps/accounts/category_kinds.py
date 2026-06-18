"""Классификация slug категорий витрины для блоков карточки."""

LAND_CATEGORY_SLUG = 'land_plot'
SUBURBAN_CATEGORY_SLUGS = frozenset({'dacha', 'cottage'})


def category_detail_kind(slug: str | None) -> str:
    """Возвращает: land_plot | suburban | residential."""
    if not slug:
        return 'residential'
    if slug == LAND_CATEGORY_SLUG:
        return 'land_plot'
    if slug in SUBURBAN_CATEGORY_SLUGS:
        return 'suburban'
    return 'residential'
