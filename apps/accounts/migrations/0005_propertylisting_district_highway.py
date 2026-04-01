from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_propertytag_remove_listing_tags_json'),
    ]

    operations = [
        migrations.AddField(
            model_name='propertylisting',
            name='district',
            field=models.CharField(
                blank=True,
                help_text='Для фильтра каталога («Домодедовский» и т.п.).',
                max_length=255,
                verbose_name='район',
            ),
        ),
        migrations.AddField(
            model_name='propertylisting',
            name='highway',
            field=models.CharField(
                blank=True,
                help_text='Ближайшее шоссе («Дмитровское» и т.п.).',
                max_length=255,
                verbose_name='шоссе',
            ),
        ),
    ]
