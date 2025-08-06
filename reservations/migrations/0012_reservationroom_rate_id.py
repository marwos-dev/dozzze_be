from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0011_alter_reservationroom_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservationroom",
            name="rate_id",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="ID de tarifa"
            ),
        ),
    ]
