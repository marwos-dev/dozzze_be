from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ('vouchers', '0002_add_reservation_field'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountCoupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='Código')),
                ('discount_percent', models.DecimalField(max_digits=5, decimal_places=2)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_coupons', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'discount_coupons',
                'verbose_name': 'Cupón de descuento',
                'verbose_name_plural': 'Cupones de descuento',
            },
        ),
    ]
