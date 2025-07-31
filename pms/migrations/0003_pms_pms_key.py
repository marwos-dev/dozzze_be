from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pms", "0002_pms_pms_external_id_pmsdataresponse"),
    ]

    operations = [
        migrations.AddField(
            model_name="pms",
            name="pms_key",
            field=models.CharField(max_length=255, unique=True, default="fnsrooms"),
            preserve_default=False,
        ),
    ]

