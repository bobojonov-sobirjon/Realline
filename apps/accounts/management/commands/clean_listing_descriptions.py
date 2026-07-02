"""
Очищает HTML в поле description у всех объектов каталога.

  python manage.py clean_listing_descriptions
  python manage.py clean_listing_descriptions --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import PropertyListing
from apps.accounts.utils.html_text import clean_listing_description


class Command(BaseCommand):
    help = 'Убирает HTML-теги и сущности из description у PropertyListing.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Только отчёт, без записи в БД.')

    @transaction.atomic
    def handle(self, *args, **options):
        updated = 0
        for listing in PropertyListing.objects.exclude(description='').iterator():
            cleaned = clean_listing_description(listing.description)
            if cleaned == listing.description:
                continue
            updated += 1
            if not options['dry_run']:
                listing.description = cleaned
                listing.save(update_fields=['description', 'updated_at'])

        if options['dry_run']:
            transaction.set_rollback(True)

        mode = '[dry-run] ' if options['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(f'{mode}Обновлено описаний: {updated}'))
