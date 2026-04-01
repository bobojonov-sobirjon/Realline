from django.db import migrations

from apps.accounts.utils.catalog_reference_data import DISTRICT_NAMES, HIGHWAY_NAMES


def expand_catalog(apps, schema_editor):
    District = apps.get_model('accounts', 'District')
    Highway = apps.get_model('accounts', 'Highway')
    for name in dict.fromkeys(DISTRICT_NAMES):
        District.objects.get_or_create(name=name)
    for name in dict.fromkeys(HIGHWAY_NAMES):
        Highway.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_district_highway_ref_data'),
    ]

    operations = [
        migrations.RunPython(expand_catalog, migrations.RunPython.noop),
    ]
