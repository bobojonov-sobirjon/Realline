# Generated manually for model sync

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_verified',
            field=models.BooleanField(
                default=False,
                help_text='Пока False — вход в личный кабинет запрещён. Superuser выставляет True в админке.',
                verbose_name='подтверждён администратором',
            ),
        ),
    ]
