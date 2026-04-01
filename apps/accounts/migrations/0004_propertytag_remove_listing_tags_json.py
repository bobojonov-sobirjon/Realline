import django.db.models.deletion
from django.db import migrations, models


def copy_json_tags_to_rows(apps, schema_editor):
    PropertyListing = apps.get_model('accounts', 'PropertyListing')
    PropertyTag = apps.get_model('accounts', 'PropertyTag')
    for listing in PropertyListing.objects.all():
        raw = listing.tags
        if not raw:
            continue
        for item in raw:
            if isinstance(item, str):
                name = item.strip()[:200]
                if name:
                    PropertyTag.objects.create(listing_id=listing.pk, tag_name=name)
            elif isinstance(item, dict):
                name = (item.get('tag_name') or item.get('name') or '').strip()[:200]
                if name:
                    PropertyTag.objects.create(listing_id=listing.pk, tag_name=name)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_agentrequest_status_linked_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropertyTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_name', models.CharField(max_length=200, verbose_name='тег')),
                (
                    'listing',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='tags',
                        to='accounts.propertylisting',
                        verbose_name='объект',
                    ),
                ),
            ],
            options={
                'verbose_name': 'тег объекта',
                'verbose_name_plural': 'теги объекта',
                'ordering': ['id'],
            },
        ),
        migrations.RunPython(copy_json_tags_to_rows, noop_reverse),
        migrations.RemoveField(
            model_name='propertylisting',
            name='tags',
        ),
    ]
