"""Совместимость: делегирует seed_website_demo (только статьи, без FAQ)."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создаёт демо-статьи. Предпочтительно: python manage.py seed_website_demo"

    def handle(self, *args, **options):
        self.stdout.write("Запуск seed_website_demo --skip-faq …")
        call_command("seed_website_demo", skip_faq=True)
