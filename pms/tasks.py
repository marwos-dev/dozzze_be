# pms/tasks.py
import json
from datetime import datetime

from celery import shared_task

from pms.utils.property_helper_factory import PMSHelperFactory
from properties.models import Availability, Property, RoomType
from reservations.models import Reservation, ReservationRoom


def _process_reservation(prop: Property, helper):
    reservations_data = helper.download_reservations(prop)
    if not reservations_data:
        return False

    reservations_to_create = []
    reservations_rooms_to_create = []
    for reservation_data in reservations_data:
        already_exist = Reservation.objects.filter(
            user=None,
            check_in=datetime.strptime(
                reservation_data["check_in"], "%Y-%m-%d"
            ).date(),
            check_out=datetime.strptime(
                reservation_data["check_out"], "%Y-%m-%d"
            ).date(),
            guest_name=reservation_data["guest_name"],
        ).exists()

        if already_exist:
            print(f"Reservation already exists for: {reservation_data}")
            continue

        occupancy = 0
        if isinstance(reservation_data["rooms"], list):
            for room in reservation_data["rooms"]:
                occupancy += int(room.get("occupancy", 0))
        else:
            occupancy = int(reservation_data["rooms"]["occupancy"])

        reservation = Reservation(
            property=prop,
            check_in=datetime.strptime(
                reservation_data["check_in"], "%Y-%m-%d"
            ).date(),
            check_out=datetime.strptime(
                reservation_data["check_out"], "%Y-%m-%d"
            ).date(),
            pax_count=occupancy,
            total_price=reservation_data["total_price"],
            paid_online=reservation_data.get("paid_online", None),
            pay_on_arrival=reservation_data.get("pay_on_arrival", None),
            channel=reservation_data.get("channel", None),
            guest_name=reservation_data.get("guest_name", None),
            guest_corporate=reservation_data.get("guest_corporate", None),
            guest_email=reservation_data.get("guest_email", None),
            guest_phone=reservation_data.get("guest_phone", None),
            guest_address=reservation_data.get("guest_address", None),
            guest_city=reservation_data.get("guest_city", None),
            guest_region=reservation_data.get("guest_region", None),
            guest_country=reservation_data.get("guest_country", None),
            guest_country_iso=reservation_data.get("guest_country_iso", None),
            guest_cp=reservation_data.get("guest_cp", None),
            guest_remarks=reservation_data.get("guest_remarks", None),
            cancellation_date=reservation_data.get("cancellation_date", None),
            modification_date=reservation_data.get("modification_date", None),
            status=reservation_data.get("status", Reservation.PENDING),
        )
        reservations_to_create.append(reservation)

        rooms = None
        if rooms:
            reservation_room = ReservationRoom(
                reservation=reservation,
                room=rooms,
                price=reservation_data.get("total_price", 0),
                guests=reservation_data["room"]["occupancy"],
            )
            reservations_rooms_to_create.append(reservation_room)

    if reservations_to_create:
        Reservation.objects.bulk_create(reservations_to_create)

    if reservations_rooms_to_create:
        ReservationRoom.objects.bulk_create(reservations_rooms_to_create)

    return True

def _process_rates_and_availability(prop: Property, helper):
    rates_and_availability = helper.download_rates_and_availability(prop)
    if not rates_and_availability:
        return False

    availabilities_to_create = []
    availabilities_to_update = []

    for rate_data in rates_and_availability:
        room_type = RoomType.objects.filter(external_id=rate_data["room_type"]).first()
        if not room_type:
            print(f"Room type not found: {rate_data['room_type']}")
            continue

        availability = Availability.objects.filter(
            property=prop,
            room_type=room_type,
            date=datetime.strptime(rate_data["date"], "%Y-%m-%d"),
        ).first()
        if availability:
            rates = json.dumps(rate_data["rates"])
            if availability.rates == rates and availability.availability == rate_data["availability"]:
                continue
            availability.rates = rates
            availability.availability = rate_data["availability"]
            availabilities_to_update.append(availability)
            continue

        availability = Availability(
            property=prop,
            room_type=room_type,
            date=datetime.strptime(rate_data["date"], "%Y-%m-%d"),
            rates=json.dumps(rate_data["rates"]),
            availability=rate_data["availability"],
        )
        availabilities_to_create.append(availability)

    if availabilities_to_update:
        Availability.objects.bulk_update(
            availabilities_to_update, ["rates", "availability"]
        )

    if availabilities_to_create:
        Availability.objects.bulk_create(availabilities_to_create)

    return True


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
            _process_reservation(prop, helper)

            # Procesar tarifas y disponibilidad
            _process_rates_and_availability(prop, helper)


            if prop.pms_data.first_sync:
                prop.pms_data.first_sync = False
                prop.pms_data.save()

            print(f"Información de {prop.name} descargada correctamente.")
            return None

        except Exception as e:
            print(f"Error procesando propiedad {prop.name}: {e}")
            return None
    return None
