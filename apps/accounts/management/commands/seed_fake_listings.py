"""
Создаёт демо-объекты PropertyListing (по умолчанию 15 шт.).

Требуется хотя бы одна категория и один район в БД (если нет — команда создаёт минимальные).

  python manage.py seed_fake_listings
  python manage.py seed_fake_listings --count 20
  python manage.py seed_fake_listings --published-only
  python manage.py seed_fake_listings --with-units   # к каждому не-участку добавить демо-лоты

Повторный запуск добавляет новые объекты (код RL-XXXX генерируется сам).
"""

from decimal import Decimal
from random import choice, randint, random, shuffle

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.management.seed_units import create_demo_units_for_listing
from apps.accounts.models import (
    District,
    Highway,
    PropertyCategory,
    PropertyListing,
    PropertyTag,
    ResidentialListingDetails,
)

User = get_user_model()

NAME_PREFIX = '[ДЕМО]'

JK_NAMES = (
    'ЖК «Солнечный квартал»',
    'ЖК «Речной бульвар»',
    'Клубный дом «Патриаршие»',
    'ЖК «Лесная симфония»',
    'ЖК «Скандинавия»',
    'ЖК «Московские ворота»',
    'ЖК «Первый квартал»',
    'ЖК «Новая Охта»',
    'ЖК «Царская площадь»',
    'ЖК «Легенда»',
    'ЖК «Остров»',
    'ЖК «Символ»',
    'ЖК «Сердцевина»',
    'ЖК «Прайм»',
    'ЖК «Квартал у реки»',
)

SETTLEMENTS = (
    'Москва',
    'Химки',
    'Красногорск',
    'Одинцово',
    'Люберцы',
)

STREETS = (
    'проспект Мировой, д. 12',
    'ул. Лесная, д. 5, корп. 2',
    'Шоссейная ул., вл. 3',
    'наб. Речная, д. 1',
    'ул. Центральная, стр. 7',
)

DEVELOPERS = ('ПИК', 'ЛСР', 'ГК «Самолёт»', 'ФСК', 'MR Group')


def _ensure_categories():
    cat, _ = PropertyCategory.objects.get_or_create(
        slug='new_building',
        defaults={'name': 'Новостройки', 'sort_order': 1},
    )
    return list(PropertyCategory.objects.exclude(slug='land_plot')[:6]) or [cat]


def _ensure_land_category():
    return PropertyCategory.objects.get_or_create(
        slug='land_plot',
        defaults={'name': 'Земельные участки', 'sort_order': 99},
    )[0]


def _ensure_districts():
    names = ['Мытищи', 'Красногорск', 'Одинцово', 'Подольск', 'Люберцы']
    for n in names:
        District.objects.get_or_create(name=n, defaults={'region': District.Region.MOSCOW})
    return list(District.objects.all()[:8])


def _ensure_highways():
    names = ['Минское шоссе', 'Новорижское шоссе', 'Киевское шоссе']
    for n in names:
        Highway.objects.get_or_create(name=n, defaults={'region': Highway.Region.MOSCOW})
    return list(Highway.objects.all()[:6])


def _ensure_agent():
    user = User.objects.filter(is_verified=True).first()
    if user:
        return user
    return User.objects.create_user(
        username='seed_listings_agent',
        email='seed_listings_agent@local.invalid',
        password='SeedListingsDemo2026!',
        is_verified=True,
    )


class Command(BaseCommand):
    help = 'Создаёт фейковые PropertyListing для каталога (по умолчанию 15).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Сколько объявлений создать (по умолчанию 15).',
        )
        parser.add_argument(
            '--published-only',
            action='store_true',
            help='Все создаваемые объекты со статусом «Опубликован».',
        )
        parser.add_argument(
            '--with-units',
            action='store_true',
            help='После каждого созданного объявления (не участок) добавить демо PropertyListingUnit.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = max(1, options['count'])
        published_only = options['published_only']
        with_units = options['with_units']

        agent = _ensure_agent()
        categories = _ensure_categories()
        land_cat = _ensure_land_category()
        districts = _ensure_districts()
        highways = _ensure_highways()

        statuses = [PropertyListing.Status.PUBLISHED] * count
        if not published_only:
            n_mod = max(1, count // 5)
            statuses[:n_mod] = [PropertyListing.Status.MODERATION] * n_mod
            shuffle(statuses)

        created_ids = []
        for i in range(count):
            cat = choice(categories + [land_cat]) if random() > 0.1 else choice(categories)
            is_land = cat.slug == 'land_plot'
            st = statuses[i] if not published_only else PropertyListing.Status.PUBLISHED

            price = Decimal(randint(35, 450) * 100_000)
            if is_land:
                price = Decimal(randint(8, 120) * 100_000)

            name = f'{NAME_PREFIX} {choice(JK_NAMES)} — {choice(["корпус A", "корпус B", "литер 1", "очередь III"])}'
            settlement = choice(SETTLEMENTS)
            district = choice(districts) if districts and not is_land else (choice(districts) if districts else None)
            highway = choice(highways) if highways and random() > 0.4 else None

            listing = PropertyListing.objects.create(
                agent=agent,
                category=cat,
                name=name,
                price=price,
                settlement=settlement,
                district=district,
                highway=highway,
                address=choice(STREETS),
                area=None if is_land else Decimal(randint(28, 220)),
                land_area=Decimal(randint(6, 45)) if is_land else None,
                distance_to_mkad_km=Decimal(str(randint(2, 45))) if random() > 0.3 else None,
                latitude=Decimal('55.75') + Decimal(str(random() * 0.08)),
                longitude=Decimal('37.60') + Decimal(str(random() * 0.12)),
                has_asphalt_roads=random() > 0.5,
                has_street_lighting=random() > 0.5,
                has_guarded_territory=random() > 0.6,
                near_shops=random() > 0.4,
                near_school_kindergarten=random() > 0.5,
                near_public_transport=random() > 0.3,
                floors=randint(5, 25) if not is_land else None,
                rooms=randint(1, 5) if not is_land else None,
                bedrooms=randint(1, 4) if not is_land and random() > 0.3 else None,
                bathrooms=randint(1, 3) if not is_land and random() > 0.4 else None,
                year_built=randint(2018, 2026) if not is_land else None,
                wall_material=choice(['', 'монолит', 'кирпич', 'монолит-кирпич']),
                finishing=choice(['', 'чистовая', 'без отделки', 'предчистовая']),
                description=(
                    'Демо-описание: благоустроенная территория, детские площадки, подземный паркинг. '
                    'Удобная транспортная доступность.'
                ),
                status=st,
                is_actual_offer=(st == PropertyListing.Status.PUBLISHED and random() > 0.75),
            )
            created_ids.append(listing.pk)

            if not is_land:
                ResidentialListingDetails.objects.create(
                    listing=listing,
                    developer=choice(DEVELOPERS),
                    completion_period_text=choice(
                        ['4 кв. 2026', '2–3 кв. 2027', 'сдан', '1 кв. 2028']
                    ),
                    housing_class=choice(['комфорт', 'бизнес', 'эконом комфорт', '']),
                    units_total=randint(200, 1200),
                    units_available=randint(10, 120),
                    price_per_sqm_from=(listing.price / listing.area).quantize(Decimal('1'))
                    if listing.area and listing.area > 0
                    else None,
                    district_note=settlement,
                )
            if st == PropertyListing.Status.PUBLISHED and random() > 0.6:
                PropertyTag.objects.create(listing=listing, tag_name=choice(['Акция', 'Старт продаж', 'С выходом в Лес']))

            if with_units and not is_land:
                create_demo_units_for_listing(listing, count=5)

        self.stdout.write(
            self.style.SUCCESS(f'Создано объявлений: {len(created_ids)} (id: {created_ids[:5]}{"..." if len(created_ids) > 5 else ""}). Агент: {agent.username}')
        )
