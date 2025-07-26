from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('vouchers', '0003_discountcoupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='discountcoupon',
            name='name',
            field=models.CharField(max_length=50, default=''),
            preserve_default=False,
        ),
    ]
