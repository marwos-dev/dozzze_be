from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('reservations', '0008_add_refunded_status'),
        ('vouchers', '0003_discountcoupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='discount_coupon',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reservations',
                to='vouchers.discountcoupon',
                null=True,
                blank=True,
            ),
        ),
    ]
