"""
Добавляет демо-лоты PropertyListingUnit для ЖК (не для land_plot).

  python manage.py seed_demo_units
  # то же, что --fill-published: всем опубликованным без лотов (удобно после seed_fake_listings на сервере)

  python manage.py seed_demo_units --listing 20
  python manage.py seed_demo_units --fill-published   # явно

Родительский объект должен быть в статусе «Опубликован» (как в каталоге).
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.accounts.management.seed_units import create_demo_units_for_listing
from apps.accounts.models import PropertyListing


class Command(BaseCommand):
    help = (
        'Добавляет демо PropertyListingUnit. Без аргументов: всем опубликованным ЖК без лотов '
        '(эквивалент --fill-published). Или: --listing ID для одного объекта.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--listing',
            type=int,
            default=None,
            metavar='ID',
            help='PK PropertyListing (должен быть published, не участок).',
        )
        parser.add_argument(
            '--fill-published',
            action='store_true',
            help='Явно: заполнить все опубликованные объекты без лотов (кроме land_plot). Без флага и без --listing поведение то же.',
        )
        parser.add_argument(
            '--per-listing',
            type=int,
            default=5,
            help='Сколько типов лотов на объект (макс. 5, по умолчанию 5).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        lid = options['listing']
        fill = options['fill_published']
        per = max(1, min(5, options['per_listing']))

        if lid is not None:
            listing = PropertyListing.objects.filter(pk=lid).first()
            if not listing:
                self.stdout.write(self.style.ERROR(f'Объект id={lid} не найден.'))
                return
            if listing.status != PropertyListing.Status.PUBLISHED:
                self.stdout.write(
                    self.style.WARNING(
                        f'id={lid} не опубликован (статус {listing.status}). Каталог /units/ вернёт 404.'
                    )
                )
            n = create_demo_units_for_listing(listing, count=per)
            if n == 0 and listing.units.exists():
                self.stdout.write(self.style.WARNING(f'У id={lid} уже есть лоты; пропуск.'))
            elif n == 0:
                self.stdout.write(self.style.WARNING('Лоты не созданы (категория участок или нет категории как land_plot).'))
            else:
                self.stdout.write(self.style.SUCCESS(f'id={lid}: создано лотов — {n}.'))
            return

        # По умолчанию (без --listing): как --fill-published
        if not fill:
            self.stdout.write('Параметры не указаны — режим заполнения всех опубликованных без лотов (--fill-published).\n')

        qs = (
            PropertyListing.objects.filter(status=PropertyListing.Status.PUBLISHED)
            .exclude(category__slug='land_plot')
            .annotate(u=Count('units'))
            .filter(u=0)
        )
        total_units = 0
        n_listings = 0
        for listing in qs:
            add = create_demo_units_for_listing(listing, count=per)
            if add:
                n_listings += 1
                total_units += add
        self.stdout.write(
            self.style.SUCCESS(
                f'Объявлений без лотов обработано: {qs.count()} '
                f'({n_listings} с созданными лотами); всего создано записей лотов: {total_units}.'
            )
        )
