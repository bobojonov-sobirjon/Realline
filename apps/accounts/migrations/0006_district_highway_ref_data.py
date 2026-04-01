from django.db import migrations, models
import django.db.models.deletion


DISTRICT_NAMES = [
    'Домодедовский',
    'Ленинский',
    'Одинцовский',
    'Красногорский',
    'Мытищинский',
    'Пушкинский',
    'Солнечногорский',
    'Истринский',
    'Раменский',
    'Люберецкий',
    'Подольский',
    'Ногинский',
    'Дмитровский',
    'Троицкий',
    'Щёлковский',
    'Коломенский',
    'Серпуховский',
    'Чеховский',
    'Волоколамский',
]

HIGHWAY_NAMES = [
    'Дмитровское',
    'Ленинградское',
    'Новорижское',
    'Калужское',
    'Киевское',
    'Минское',
    'Волоколамское',
    'Горьковское',
    'Рязанское',
    'Симферопольское',
    'Варшавское',
    'Ярославское',
    'Щёлковское',
    'Рублёво-Успенское',
    'Новорязанское',
    'Сколковское',
    'Пятницкое',
    'Алтуфьевское',
    'Осташковское',
]


def seed_reference(apps, schema_editor):
    District = apps.get_model('accounts', 'District')
    Highway = apps.get_model('accounts', 'Highway')
    for n in DISTRICT_NAMES:
        District.objects.get_or_create(name=n)
    for n in HIGHWAY_NAMES:
        Highway.objects.get_or_create(name=n)


def backfill_fk(apps, schema_editor):
    PropertyListing = apps.get_model('accounts', 'PropertyListing')
    District = apps.get_model('accounts', 'District')
    Highway = apps.get_model('accounts', 'Highway')
    for row in PropertyListing.objects.all():
        updates = {}
        legacy_d = (row.district_legacy or '').strip()
        legacy_h = (row.highway_legacy or '').strip()
        if legacy_d:
            d = District.objects.filter(name__iexact=legacy_d).first()
            if d:
                updates['district_id'] = d.pk
        if legacy_h:
            h = Highway.objects.filter(name__iexact=legacy_h).first()
            if h:
                updates['highway_id'] = h.pk
        if updates:
            PropertyListing.objects.filter(pk=row.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_propertylisting_district_highway'),
    ]

    operations = [
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='название')),
            ],
            options={
                'verbose_name': 'район',
                'verbose_name_plural': 'районы',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Highway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='название')),
            ],
            options={
                'verbose_name': 'шоссе',
                'verbose_name_plural': 'шоссе',
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(seed_reference, migrations.RunPython.noop),
        migrations.RenameField(
            model_name='propertylisting',
            old_name='district',
            new_name='district_legacy',
        ),
        migrations.RenameField(
            model_name='propertylisting',
            old_name='highway',
            new_name='highway_legacy',
        ),
        migrations.AddField(
            model_name='propertylisting',
            name='district',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='listings',
                to='accounts.district',
                verbose_name='район',
            ),
        ),
        migrations.AddField(
            model_name='propertylisting',
            name='highway',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='listings',
                to='accounts.highway',
                verbose_name='шоссе',
            ),
        ),
        migrations.RunPython(backfill_fk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='propertylisting',
            name='district_legacy',
        ),
        migrations.RemoveField(
            model_name='propertylisting',
            name='highway_legacy',
        ),
    ]
