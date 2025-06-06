# Generated by Django 5.2.1 on 2025-06-02 20:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pms', '0002_pms_pms_external_id'),
        ('properties', '0006_remove_property_base_url_remove_property_email_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pmsdataproperty',
            name='pms',
        ),
        migrations.AddField(
            model_name='property',
            name='pms',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='properties', to='pms.pms', verbose_name='PMS'),
        ),
    ]
