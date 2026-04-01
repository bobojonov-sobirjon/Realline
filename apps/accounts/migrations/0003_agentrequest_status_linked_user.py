# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_customuser_is_verified'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentrequest',
            name='linked_user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='source_agent_request',
                to=settings.AUTH_USER_MODEL,
                verbose_name='созданный агент',
            ),
        ),
        migrations.AddField(
            model_name='agentrequest',
            name='status',
            field=models.CharField(
                choices=[('new', 'Новая заявка'), ('cabinet_created', 'Кабинет создан')],
                default='new',
                max_length=32,
                verbose_name='статус',
            ),
        ),
    ]
