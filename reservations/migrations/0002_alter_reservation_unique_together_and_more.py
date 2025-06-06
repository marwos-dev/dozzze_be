# Generated by Django 5.2.1 on 2025-06-04 19:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0012_pmsdataproperty_pms_property_address_and_more'),
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='reservation',
            name='cancellation_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Cancellation date'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='channel',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre del channel'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='channel_id',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='ID del channel'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='currency',
            field=models.CharField(default='EUR', max_length=3, verbose_name='Moneda'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='guest_address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Dirección del huésped'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='guest_city',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Ciudad del huésped'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='guest_corporate',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre de la empresa del huésped'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='guest_country',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='País del huésped'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='guest_country_iso',
            field=models.CharField(blank=True, default='US', max_length=4, null=True, verbose_name='País del huésped (ISO)'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='guest_region',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Región del huésped'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='modification_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Modification date'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='paid_online',
            field=models.FloatField(blank=True, null=True, verbose_name='Paid online'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='pay_on_arrival',
            field=models.FloatField(blank=True, null=True, verbose_name='Pay on arrival'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='total_price',
            field=models.FloatField(blank=True, null=True, verbose_name='Total price'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='check_in',
            field=models.DateField(blank=True, null=True, verbose_name='Checkin'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='check_out',
            field=models.DateField(blank=True, null=True, verbose_name='Checkout'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='guest_email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email del huésped'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='guest_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre del huésped'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='guest_phone',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Teléfono del huésped'),
        ),
        migrations.CreateModel(
            name='ReservationRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField(blank=True, null=True)),
                ('guests', models.IntegerField(default=1, verbose_name='Cantidad de huéspedes')),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reservations.reservation')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='properties.room')),
            ],
            options={
                'verbose_name': 'Habitación reservada',
                'verbose_name_plural': 'Habitaciones reservadas',
                'unique_together': {('reservation', 'room')},
            },
        ),
        migrations.AddField(
            model_name='reservation',
            name='rooms',
            field=models.ManyToManyField(related_name='reservations', through='reservations.ReservationRoom', to='properties.room'),
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='room',
        ),
    ]
