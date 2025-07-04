
# Generated by Django 5.2.1 on 2025-06-24 18:34
from django.contrib.auth import get_user_model
from django.db import migrations
from properties.models import Property


def set_admin_as_owner(apps, schema_editor):
    try:
        admin_user = get_user_model().objects.filter(is_superuser=True).first()
        if not admin_user:
            return  # Si no hay superuser, no hacemos nada

        Property.objects.filter(owner__isnull=True).update(owner=admin_user)
    except Exception as e:
        print(f"Error al asignar owner: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0003_property_owner"),
    ]

    operations = [
        migrations.RunPython(set_admin_as_owner),
    ]

