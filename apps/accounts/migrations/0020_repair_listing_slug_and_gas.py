# Repair: slug/gas_supply/suburban table if migrations were faked without DB changes.

from django.db import migrations, models
from django.utils.text import slugify

_CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}

_ADD_SLUG_COLUMN = """
ALTER TABLE accounts_propertylisting
ADD COLUMN IF NOT EXISTS slug varchar(64) NOT NULL DEFAULT '';
"""

_ENSURE_SLUG_UNIQUE = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE t.relname = 'accounts_propertylisting'
          AND c.conname = 'accounts_propertylisting_slug_key'
    ) THEN
        ALTER TABLE accounts_propertylisting
        ADD CONSTRAINT accounts_propertylisting_slug_key UNIQUE (slug);
    END IF;
END $$;
"""

_ENSURE_SLUG_LIKE_INDEX = """
CREATE INDEX IF NOT EXISTS accounts_propertylisting_slug_9b014f79_like
ON accounts_propertylisting (slug varchar_pattern_ops);
"""

_ADD_GAS_SUPPLY = """
ALTER TABLE accounts_propertylisting
ADD COLUMN IF NOT EXISTS gas_supply varchar(255) NOT NULL DEFAULT '';
"""


def _transliterate_ru(text: str) -> str:
    out = []
    for ch in (text or '').lower():
        out.append(_CYRILLIC_TO_LATIN.get(ch, ch))
    return ''.join(out)


def _slug_base(name: str, code: str = '') -> str:
    base = slugify(_transliterate_ru(name or ''))[:50].strip('-')
    if not base and code:
        base = slugify(_transliterate_ru(code))[:50].strip('-')
    return base or 'listing'


def backfill_slugs_if_empty(apps, schema_editor):
    PropertyListing = apps.get_model('accounts', 'PropertyListing')
    used = set(PropertyListing.objects.exclude(slug='').values_list('slug', flat=True))
    for obj in PropertyListing.objects.all().order_by('pk'):
        if (obj.slug or '').strip():
            continue
        base = _slug_base(obj.name, obj.code)
        candidate = base
        n = 0
        while candidate in used:
            n += 1
            candidate = f'{base}-{n}'
        obj.slug = candidate
        used.add(candidate)
        PropertyListing.objects.filter(pk=obj.pk).update(slug=candidate)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0019_suburban_listing_details'),
    ]

    operations = [
        migrations.RunSQL(sql=_ADD_SLUG_COLUMN, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(sql=_ADD_GAS_SUPPLY, reverse_sql=migrations.RunSQL.noop),
        migrations.RunPython(backfill_slugs_if_empty, noop),
        migrations.RunSQL(sql=_ENSURE_SLUG_UNIQUE, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(sql=_ENSURE_SLUG_LIKE_INDEX, reverse_sql=migrations.RunSQL.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='propertylisting',
                    name='gas_supply',
                    field=models.CharField(blank=True, max_length=255, verbose_name='газ'),
                ),
            ],
        ),
    ]
