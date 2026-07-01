"""
Находит ЖК, заведённые в каталоге несколько раз (ostrov-pervyh, ostrov-pervyh-1, …),
оставляет одну карточку с лотами и удаляет остальные.

  python manage.py cleanup_duplicate_listings
  python manage.py cleanup_duplicate_listings --execute
  python manage.py cleanup_duplicate_listings --execute --reimport
  python manage.py cleanup_duplicate_listings --name "Остров"
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.management.listing_dedupe import (
    apply_cleanup,
    find_duplicate_groups,
    load_known_guids,
)
from apps.accounts.management.trendagent_import import import_all
from apps.accounts.models import PropertyListing
from apps.accounts.utils.region import normalize_listing_region


class Command(BaseCommand):
    help = (
        'Ищет дубликаты PropertyListing (один ЖК — несколько карточек) '
        'и оставляет каноническую запись (slug без -N, с лотами, из TrendAgent).'
    )

    def add_arguments(self, parser):
        default_path = Path(settings.BASE_DIR) / 'data' / 'trendagent_export'
        parser.add_argument('--execute', action='store_true', help='Удалить дубликаты (без флага — только отчёт).')
        parser.add_argument('--path', type=Path, default=default_path, help='Папка trendagent_export для guid.')
        parser.add_argument('--name', default=None, help='Фильтр по части названия ЖК.')
        parser.add_argument(
            '--region',
            default=None,
            help='Фильтр региона: moscow / spb / saint_petersburg.',
        )
        parser.add_argument(
            '--reimport',
            action='store_true',
            help='После очистки переимпортировать затронутые ЖК из trendagent_export.',
        )
        parser.add_argument('--agent', default=None, help='Username агента для --reimport.')

    def handle(self, *args, **options):
        qs = PropertyListing.objects.all()
        if options['name']:
            qs = qs.filter(name__icontains=options['name'])
        if options['region']:
            region = normalize_listing_region(options['region'])
            if not region:
                self.stderr.write(self.style.ERROR(f'Неизвестный регион: {options["region"]!r}'))
                return
            qs = qs.filter(region=region)

        known_guids = load_known_guids(options['path'])
        groups = find_duplicate_groups(qs, known_guids=known_guids)

        if not groups:
            self.stdout.write(self.style.SUCCESS('Дубликатов не найдено.'))
            return

        mode = 'УДАЛЕНИЕ' if options['execute'] else 'ОТЧЁТ (dry-run)'
        self.stdout.write(self.style.WARNING(f'{mode}: найдено групп дубликатов — {len(groups)}'))
        if known_guids:
            self.stdout.write(f'Известных guid из экспорта: {len(known_guids)}')

        guids_to_reimport: set[str] = set()
        for group in groups:
            canonical = group.canonical
            self.stdout.write('')
            self.stdout.write(
                f'• {canonical.name} ({group.match_reason}) — всего {len(group.listings)} карточек'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ОСТАВИТЬ: {canonical.code} slug={canonical.slug} '
                    f'лотов={canonical.units.count()} цена={canonical.price}'
                )
            )
            for listing in group.to_remove:
                self.stdout.write(
                    f'  удалить: {listing.code} slug={listing.slug} '
                    f'лотов={listing.units.count()} цена={listing.price}'
                )
            slug = (canonical.slug or '').strip().lower()
            if slug in known_guids:
                guids_to_reimport.add(slug)

        with transaction.atomic():
            stats = apply_cleanup(groups, execute=options['execute'])
            if options['reimport'] and options['execute'] and guids_to_reimport:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING(f'Переимпорт {len(guids_to_reimport)} ЖК…'))
                for guid in sorted(guids_to_reimport):
                    results = import_all(
                        options['path'],
                        guid=guid,
                        agent_username=options['agent'],
                        publish=True,
                        replace_units=True,
                        replace_images=False,
                    )
                    for row in results:
                        self.stdout.write(
                            f'  • {row.get("name") or guid}: {row.get("units", 0)} лотов'
                            + (f' — {row["error"]}' if row.get('error') else '')
                        )

            if not options['execute']:
                transaction.set_rollback(True)

        self.stdout.write('')
        if options['execute']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Готово: групп {stats["groups"]}, удалено карточек {stats["removed"]}, '
                    f'лотов в удалённых {stats["removed_units"]}, оставлено {stats["kept"]}.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Будет удалено карточек: {stats["removed"]} '
                    f'(лотов в них: {stats["removed_units"]}). '
                    'Запустите с --execute для применения.'
                )
            )
