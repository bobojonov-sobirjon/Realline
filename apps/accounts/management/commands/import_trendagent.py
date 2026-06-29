"""
Импорт выгрузки TrendAgent (scripts/parse_trendagent.py) в каталог Django.

  python manage.py import_trendagent
  python manage.py import_trendagent --dry-run
  python manage.py import_trendagent --region saint_petersburg
  python manage.py import_trendagent --guid astrum
  python manage.py import_trendagent --path data/trendagent_export --agent admin
  python manage.py import_trendagent --moderation   # без публикации

Перед импортом желательно: python manage.py seed_region_reference --only spb
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.management.trendagent_import import import_all
from apps.accounts.utils.region import normalize_listing_region


class Command(BaseCommand):
    help = 'Импортирует ЖК и квартиры из data/trendagent_export/ в PropertyListing.'

    def add_arguments(self, parser):
        default_path = Path(settings.BASE_DIR) / 'data' / 'trendagent_export'
        parser.add_argument('--path', type=Path, default=default_path, help='Папка экспорта.')
        parser.add_argument(
            '--region',
            default=None,
            help='Фильтр региона: moscow, msk, мск, spb, спб, saint_petersburg, «Это по спб»…',
        )
        parser.add_argument('--guid', default=None, help='Только один ЖК (slug/guid).')
        parser.add_argument('--agent', default=None, help='Username агента-владельца объектов.')
        parser.add_argument(
            '--moderation',
            action='store_true',
            help='Статус «На модерации» вместо «Опубликован».',
        )
        parser.add_argument(
            '--keep-units',
            action='store_true',
            help='Не удалять существующие лоты перед импортом.',
        )
        parser.add_argument(
            '--keep-images',
            action='store_true',
            help='Не заменять галерею объекта.',
        )
        parser.add_argument('--dry-run', action='store_true', help='Только подсчёт без записи в БД.')

    @transaction.atomic
    def handle(self, *args, **options):
        export_root: Path = options['path']
        if not export_root.is_dir():
            raise CommandError(f'Папка не найдена: {export_root}')

        region_filter = normalize_listing_region(options['region']) if options['region'] else None
        if options['region'] and not region_filter:
            raise CommandError(
                f'Неизвестный регион: {options["region"]!r}. '
                'Используйте moscow / msk / мск или spb / спб / saint_petersburg.'
            )

        try:
            results = import_all(
                export_root,
                region=region_filter,
                guid=options['guid'],
                agent_username=options['agent'],
                publish=not options['moderation'],
                replace_units=not options['keep_units'],
                replace_images=not options['keep_images'],
                dry_run=options['dry_run'],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if not results:
            self.stdout.write(self.style.WARNING('Нечего импортировать (проверьте --path / --region / --guid).'))
            return

        created = sum(1 for r in results if r.get('created'))
        updated = sum(1 for r in results if r.get('updated'))
        units = sum(r.get('units', 0) for r in results)
        images = sum(r.get('images', 0) for r in results)
        errors = [r for r in results if r.get('error')]

        mode = '[dry-run] ' if options['dry_run'] else ''
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode}ЖК: {len(results)} (новых {created}, обновлено {updated}); '
                f'лотов {units}; фото ЖК {images}.'
            )
        )
        for row in results:
            line = f"  • {row.get('name') or row.get('guid')}: {row.get('units', 0)} лотов, {row.get('images', 0)} фото"
            if row.get('error'):
                line += f" — {row['error']}"
            self.stdout.write(line)

        if errors:
            raise CommandError(f'Ошибки: {len(errors)} ЖК не импортированы.')
