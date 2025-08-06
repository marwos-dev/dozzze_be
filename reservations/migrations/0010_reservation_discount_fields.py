from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0009_discount_coupon_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="original_price",
            field=models.FloatField(
                blank=True, null=True, verbose_name="Original price"
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="discount_amount",
            field=models.FloatField(default=0, verbose_name="Discount amount"),
        ),
    ]
