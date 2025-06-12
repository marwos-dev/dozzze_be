# pms/tasks.py

from celery import shared_task

from pms.utils.property_helper_factory import PMSHelperFactory
from properties.models import Property
from properties.sync_service import SyncService


@shared_task
def sync_fns_data():
    props = Property.objects.all()
    for prop in props:
        try:
            _continue = True
            necesary_fields = [
                "pms_token",
                "pms_hotel_identifier",
                "pms_username",
                "pms_password",
                "email",
                "phone_number",
                "base_url",
            ]
            for field in necesary_fields:
                if not getattr(prop.pms_data, field):
                    print(f"Falta el campo {field} en la propiedad {prop.name}")
                    _continue = False

            if not _continue:
                continue

            print(f"Descargando info de {prop.name}...")
            factory = PMSHelperFactory()
            helper = factory.get_helper(prop)
            if not helper:
                print(f"No se encontró un helper para la propiedad {prop.name}")
                continue

            # Procesar reservas
            SyncService.sync_reservations(prop, helper)

            # Procesar tarifas y disponibilidad
            SyncService.sync_rates_and_availability(prop, helper)

            if prop.pms_data.first_sync:
                prop.pms_data.first_sync = False
                prop.pms_data.save()

            print(f"Información de {prop.name} descargada correctamente.")
            return None

        except Exception as e:
            print(f"Error procesando propiedad {prop.name}: {e}")
            return None
    return None
