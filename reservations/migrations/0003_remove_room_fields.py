from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0002_alter_reservation_unique_together_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="reservationroom",
            name="room",
        ),
        migrations.AlterField(
            model_name="reservationroom",
            name="reservation",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="reservation_rooms",
                to="reservations.reservation",
            ),
        ),
        migrations.RemoveField(
            model_name="reservation",
            name="rooms",
        ),
        migrations.AddField(
            model_name="reservation",
            name="room_types",
            field=models.ManyToManyField(
                related_name="reservations",
                through="reservations.ReservationRoom",
                to="properties.roomtype",
            ),
        ),
    ]
