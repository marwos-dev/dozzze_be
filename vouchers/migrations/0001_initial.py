from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='Código')),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto original')),
                ('remaining_amount', models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto restante')),
                ('active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_vouchers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'vouchers',
                'verbose_name': 'Voucher',
                'verbose_name_plural': 'Vouchers',
            },
        ),
        migrations.CreateModel(
            name='VoucherRedemption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(max_digits=10, decimal_places=2)),
                ('redeemed_at', models.DateTimeField(auto_now_add=True)),
                ('voucher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='redemptions', to='vouchers.voucher')),
            ],
            options={
                'db_table': 'voucher_redemptions',
                'verbose_name': 'Canjeo',
                'verbose_name_plural': 'Canjeos',
            },
        ),
    ]
