"""Общая логика демо-лотов (PropertyListingUnit) для management-команд."""

from decimal import Decimal
from random import choice, randint

from apps.accounts.models import PropertyListingUnit

BUILDINGS = ('корп. 1', 'корп. 2', 'литер А', 'литер Б')

_LAYOUT_SPECS = [
    ('Студия', True, None, Decimal('28.5'), Decimal('8.2')),
    ('1-комнатная', False, 1, Decimal('38.2'), Decimal('12.0')),
    ('2-комнатная', False, 2, Decimal('58.7'), Decimal('14.5')),
    ('3-комнатная', False, 3, Decimal('78.4'), Decimal('16.0')),
    ('4-комнатная', False, 4, Decimal('99.0'), Decimal('18.5')),
]


def create_demo_units_for_listing(listing, count: int = 5) -> int:
    """Возвращает число созданных лотов; 0 если участок или лоты уже есть."""
    slug = getattr(listing.category, 'slug', None) or ''
    if slug == 'land_plot':
        return 0
    if listing.units.exists():
        return 0

    n = max(1, min(count, len(_LAYOUT_SPECS)))
    chosen = _LAYOUT_SPECS[:n]

    base = listing.price if listing.price else Decimal('15_000_000')
    created = 0
    for order, (label, is_studio, rooms, area, kitchen) in enumerate(chosen):
        k = Decimal('0.85') + Decimal(str(order)) * Decimal('0.07')
        price = (base * k).quantize(Decimal('1'))
        PropertyListingUnit.objects.create(
            listing=listing,
            layout_label=label,
            title='Квартира' if not is_studio else 'Студия',
            building=choice(BUILDINGS),
            completion_text=choice(['4 кв. 2026', '2 кв. 2027', 'сдан']),
            keys_handover_text=choice(['по готовности', 'через 14 дней после сделки']),
            rooms=rooms,
            is_studio=is_studio,
            price=price,
            total_area=area,
            kitchen_area=kitchen,
            floor=randint(2, 18),
            floors_total=randint(18, 25),
            finishing=choice(['чистовая', 'без отделки', 'white box']),
            bathroom_summary=choice(['совмещённый', 'раздельный', '2 с/у']),
            ceiling_height='2.75 м',
            balcony_summary=choice(['лоджия', 'балкон', 'нет']),
            sort_order=order,
        )
        created += 1
    return created
