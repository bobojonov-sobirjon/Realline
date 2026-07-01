"""
Находит ЖК, заведённые в каталоге несколько раз, оставляет одну карточку и удаляет остальные.

Поддерживаемые паттерны дубликатов:
  ostrov-pervyh, ostrov-pervyh-1, ostrov-pervyh-26
  1733, 1733-dced35, 1733-a1b2c3
  moiseenko-10, moiseenko-10-a0be81
  zhk-mira, zhk-mira-f32b79

  python manage.py cleanup_duplicate_listings
  python manage.py cleanup_duplicate_listings --execute
  python manage.py cleanup_duplicate_listings --execute --reimport
  python manage.py cleanup_duplicate_listings --name "17/33"
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.management.listing_dedupe import (
    apply_cleanup,
    find_duplicate_groups,
    load_known_guids,
    normalize_canonical_slugs,
)
from apps.accounts.management.trendagent_import import import_all
from apps.accounts.models import PropertyListing
from apps.accounts.utils.region import normalize_listing_region


class Command(BaseCommand):
    help = (
        'Ищет дубликаты PropertyListing (один ЖК — несколько карточек), '
        'нормализует slug, удаляет лишние и при --execute переимпортирует лоты из TrendAgent.'
    )

    def add_arguments(self, parser):
        default_path = Path(settings.BASE_DIR) / 'data' / 'trendagent_export'
        parser.add_argument('--execute', action='store_true', help='Применить изменения (без флага — только отчёт).')
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
            help='После очистки переимпортировать лоты из trendagent_export (по умолчанию вместе с --execute).',
        )
        parser.add_argument(
            '--no-reimport',
            action='store_true',
            help='Не переимпортировать лоты даже при --execute.',
        )
        parser.add_argument('--agent', default=None, help='Username агента для переимпорта.')

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

        export_root: Path = options['path']
        known_guids = load_known_guids(export_root)
        groups = find_duplicate_groups(qs, known_guids=known_guids)

        if not groups:
            self.stdout.write(self.style.SUCCESS('Дубликатов не найдено.'))
            return

        do_reimport = (
            options['execute']
            and not options['no_reimport']
            and (options['reimport'] or export_root.is_dir())
        )

        mode = 'УДАЛЕНИЕ' if options['execute'] else 'ОТЧЁТ (dry-run)'
        self.stdout.write(self.style.WARNING(f'{mode}: найдено групп дубликатов — {len(groups)}'))
        if known_guids:
            self.stdout.write(f'Известных guid из экспорта: {len(known_guids)}')
        if do_reimport:
            self.stdout.write('После очистки: переимпорт лотов из trendagent_export')

        guids_to_reimport: set[str] = set()
        for group in groups:
            canonical = group.canonical
            self.stdout.write('')
            self.stdout.write(
                f'• {canonical.name} ({group.match_reason}) — всего {len(group.listings)} карточек'
            )
            target_slug = group.cluster_key or canonical.slug
            self.stdout.write(
                self.style.SUCCESS(
                    f'  ОСТАВИТЬ: {canonical.code} slug={canonical.slug} → {target_slug} '
                    f'лотов={canonical.units.count()} цена={canonical.price}'
                )
            )
            for listing in group.to_remove:
                self.stdout.write(
                    f'  удалить: {listing.code} slug={listing.slug} '
                    f'лотов={listing.units.count()} цена={listing.price}'
                )
            if group.reimport_guid:
                guids_to_reimport.add(group.reimport_guid)

        with transaction.atomic():
            renamed = normalize_canonical_slugs(groups, known_guids, execute=options['execute'])
            stats = apply_cleanup(groups, execute=options['execute'])
            stats['renamed'] = renamed

            if do_reimport and guids_to_reimport:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING(f'Переимпорт {len(guids_to_reimport)} ЖК…'))
                for guid in sorted(guids_to_reimport):
                    results = import_all(
                        export_root,
                        guid=guid,
                        agent_username=options['agent'],
                        publish=True,
                        replace_units=True,
                        replace_images=False,
                    )
                    if not results:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  • {guid}: нет данных в {export_root} — пропуск'
                            )
                        )
                        continue
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
                    f'Готово: групп {stats["groups"]}, slug исправлено {stats["renamed"]}, '
                    f'удалено карточек {stats["removed"]}, лотов в удалённых {stats["removed_units"]}, '
                    f'оставлено {stats["kept"]}.'
                )
            )
            if guids_to_reimport and not do_reimport:
                self.stdout.write(
                    self.style.WARNING(
                        'Переимпорт пропущен: нет папки экспорта или указан --no-reimport.'
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Будет удалено карточек: {stats["removed"]} '
                    f'(лотов в них: {stats["removed_units"]}). '
                    'Запустите: python manage.py cleanup_duplicate_listings --execute'
                )
            )
