from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0011_alter_service_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="code",
            field=models.CharField(max_length=100, unique=True, verbose_name="Código"),
        ),
        migrations.AlterField(
            model_name="service",
            name="description",
            field=models.TextField(blank=True, verbose_name="Descripción"),
        ),
        migrations.AlterUniqueTogether(
            name="service",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="service",
            name="property",
        ),
        migrations.CreateModel(
            name="PropertyService",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "property",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="property_services",
                        to="properties.property",
                        verbose_name="Propiedad",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="property_services",
                        to="properties.service",
                        verbose_name="Servicio",
                    ),
                ),
            ],
            options={
                "db_table": "property_services",
                "verbose_name": "Servicio de Propiedad",
                "verbose_name_plural": "Servicios de Propiedades",
                "unique_together": {("property", "service")},
            },
        ),
        migrations.AddField(
            model_name="property",
            name="services",
            field=models.ManyToManyField(
                blank=True,
                related_name="properties",
                through="properties.PropertyService",
                to="properties.service",
                verbose_name="Servicios",
            ),
        ),
    ]

