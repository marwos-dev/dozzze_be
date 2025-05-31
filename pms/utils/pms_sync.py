# pms_sync.py


def sync_property_with_pms(property_obj):
    """
    Según el PMS vinculado, realiza una llamada API para obtener habitaciones y reservas
    y las guarda en la base de datos.
    """
    if not property_obj.pms:
        raise Exception("La propiedad no tiene un PMS asignado")

    pms_type = property_obj.pms.name.lower()

    if pms_type == "pms1":
        return sync_with_pms1(property_obj)
    elif pms_type == "cloudbeds":
        print("hola")
        # return sync_with_cloudbeds(property_obj)
    else:
        raise Exception(f"No hay integración definida para el PMS '{pms_type}'")


def sync_with_pms1(property_obj):
    """
    Ejemplo de sincronización con un PMS personalizado.
    """
    # Simulamos llamada a API, parseo y guardado
    print("Sincronizando habitaciones y reservas...")

    # TODO: traer datos reales
    # habitaciones = api.get_rooms(...)
    # reservas = api.get_reservations(...)

    # for hab in habitaciones:
    #     Room.objects.create(...) o update_or_create
    #
    # for res in reservas:
    #     Reservation.objects.create(...) o update_or_create

    return True
