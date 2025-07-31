from django.db import migrations


def set_pms_key(apps, schema_editor):
    PMS = apps.get_model("pms", "PMS")
    # Ensure existing records have a value for ``pms_key``.
    PMS.objects.all().update(pms_key="fnsrooms")


class Migration(migrations.Migration):

    dependencies = [
        ("pms", "0003_pms_pms_key"),
    ]

    operations = [
        migrations.RunPython(set_pms_key, migrations.RunPython.noop),
    ]
