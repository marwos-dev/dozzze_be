from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('reservations', '0006_alter_reservationroom_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending'),
                    ('confirmed', 'Confirmed'),
                    ('pending_refund', 'Pending refund'),
                    ('cancelled', 'Cancelled'),
                    ('ok', 'Ok'),
                ],
                default='pending',
                verbose_name='Estado',
            ),
        ),
    ]
