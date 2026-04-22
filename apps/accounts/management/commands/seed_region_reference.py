"""
Seed reference lists for District/Highway limited to two regions:
- Moscow
- Saint Petersburg

Usage:
  python manage.py seed_region_reference
  python manage.py seed_region_reference --only spb
  python manage.py seed_region_reference --only moscow
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import District, Highway


MOSCOW_DISTRICTS = (
    'Тверской',
    'Пресненский',
    'Хамовники',
    'Арбат',
    'Басманный',
    'Таганский',
    'Замоскворечье',
)

SPB_DISTRICTS = (
    'Центральный',
    'Петроградский',
    'Василеостровский',
    'Адмиралтейский',
    'Приморский',
    'Московский район (СПб)',
    'Невский',
)

MOSCOW_HIGHWAYS = (
    'Ленинградское',
    'Киевское',
    'Минское',
    'Новорижское',
    'Ярославское',
    'Дмитровское',
)

SPB_HIGHWAYS = (
    'КАД',
    'ЗСД',
    'Московское шоссе (СПб)',
    'Пулковское шоссе',
    'Приморское шоссе',
    'Выборгское шоссе',
)


class Command(BaseCommand):
    help = 'Создаёт справочники District/Highway только для Moscow и Saint Petersburg.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            choices=('moscow', 'spb'),
            default=None,
            help='Создавать только для одного региона: moscow или spb.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        only = options.get('only')

        created_d = 0
        created_h = 0

        def _seed_region(*, region: str, districts: tuple[str, ...], highways: tuple[str, ...]):
            nonlocal created_d, created_h
            for name in districts:
                _, created = District.objects.get_or_create(
                    name=name,
                    defaults={'region': region},
                )
                if created:
                    created_d += 1
            for name in highways:
                _, created = Highway.objects.get_or_create(
                    name=name,
                    defaults={'region': region},
                )
                if created:
                    created_h += 1

        if only in (None, 'moscow'):
            _seed_region(
                region=District.Region.MOSCOW,
                districts=MOSCOW_DISTRICTS,
                highways=MOSCOW_HIGHWAYS,
            )

        if only in (None, 'spb'):
            _seed_region(
                region=District.Region.SAINT_PETERSBURG,
                districts=SPB_DISTRICTS,
                highways=SPB_HIGHWAYS,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово. Создано District: {created_d}, Highway: {created_h}.'
            )
        )

