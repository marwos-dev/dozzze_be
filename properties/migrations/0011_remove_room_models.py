from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0010_alter_room_description"),
    ]

    operations = [
        migrations.DeleteModel(name="RoomImage"),
        migrations.DeleteModel(name="Room"),
    ]
