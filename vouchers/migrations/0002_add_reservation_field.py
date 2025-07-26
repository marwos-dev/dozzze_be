from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('reservations', '0008_add_refunded_status'),
        ('vouchers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucherredemption',
            name='reservation',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='voucher_redemptions',
                to='reservations.reservation',
                null=True,
                blank=True,
            ),
        ),
    ]
