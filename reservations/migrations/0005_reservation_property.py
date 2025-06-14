# Generated by Django 5.2.1 on 2025-06-05 19:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0014_pmsdataproperty_first_sync'),
        ('reservations', '0004_alter_reservation_status_alter_reservationroom_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='property',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='properties.property', verbose_name='Propiedad'),
        ),
    ]
