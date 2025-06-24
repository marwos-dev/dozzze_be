from datetime import timedelta

from django.db import transaction
from ninja import Router
from ninja.errors import HttpError

from properties.models import Availability, Property, Room
from utils import ErrorSchema, SuccessSchema
from .models import Reservation, ReservationRoom
from .schemas import ReservationSchema

router = Router(tags=["reservations"])


@router.post("/", response={200: SuccessSchema, 400: ErrorSchema})
def create_reservation(
        request,
        data: ReservationSchema
):
    try:
        check_in = data.check_in
        check_out = data.check_out
        room_ids = data.room_ids
        property_id = data.project_id

        with transaction.atomic():
            property = Property.objects.get(id=property_id)  # noqa # get for validation
            for room_id in room_ids:
                room = Room.objects.get(id=room_id)
                overlapping = Reservation.objects.filter(
                    room=room,
                    reservation__check_in=check_in,
                    reservation__check_out=check_out
                )
                if overlapping.exists():
                    raise HttpError(400, f"Room {room.name} is already reserved for the selected dates.")

            room_objs = room.objects.select_related("type").filter(id__in=room_ids)
            room_types_map = {}
            for room in room_objs:
                room_types_map.setdefault(room.type, []).append(room)

            current_date = check_in
            while current_date < check_out:
                for room_type_id, rooms in room_types_map.items():
                    availability = Availability.objects.select_for_update().get(
                        date=current_date,
                        room_type_id=room_type_id,
                        property_id=property_id,
                    )
                    if availability.availability < len(rooms):
                        raise HttpError(400, f"Not enough availability for room type {room_type_id} on {current_date}.")

                current_date += timedelta(days=1)

            current_date = check_in
            while current_date < check_out:
                for room_type_id, rooms in room_types_map.items():
                    availability = Availability.objects.select_for_update().get(
                        date=current_date,
                        room_type_id=room_type_id,
                        property_id=property_id,
                    )
                    availability.availability -= len(rooms)
                    availability.save()
                current_date += timedelta(days=1)

            # Crear la reserva
            reservation = Reservation.objects.create(
                property_id=property_id,
                check_in=check_in,
                check_out=check_out,
                pax_count=data.pax_count,
                guest_name=data.guest_name,
                guest_email=data.guest_email,
                guest_phone=data.guest_phone,
                guest_country=data.guest_country,
                guest_country_iso=data.guest_country_iso,
                guest_cp=data.guest_cp,
                guest_city=data.guest_city,
                guest_region=data.guest_region,
                guest_address=data.guest_address,
                guest_remarks=data.guest_remarks,
                user=request.user if request.user.is_authenticated else None,
                total_price=data.total_price,
                paid_online=data.paid_online,
                pay_on_arrival=data.pay_on_arrival,
                status=Reservation.PENDING,
                channel=data.channel,
                channel_id=data.channel_id,
            )

            for room in room_objs:
                ReservationRoom.objects.create(
                    reservation=reservation,
                    room=room,
                    guests=data.pax_count,  # o 1 por habitación
                    price=None,  # si querés guardar el rate acá
                )

            return {"success": True}

    except Availability.DoesNotExist:
        raise HttpError(400, "Availability for the selected dates does not exist.")
    except Room.DoesNotExist:
        raise HttpError(400, "Room does not exist.")
    except Property.DoesNotExist:
        raise HttpError(400, "Property does not exist.")
    except Exception as e:
        raise HttpError(400, f"An error occurred while creating the reservation: {str(e)}")
