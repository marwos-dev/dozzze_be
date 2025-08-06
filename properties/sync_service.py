# app/availability/services.py
import json
from datetime import datetime

from reservations.models import Reservation, ReservationRoom
from utils import extract_pax

from .models import Availability, Property, Room, RoomType


class SyncService:
    @classmethod
    def sync_rates_and_availability(
        cls, prop: Property, helper, checkin=None, checkout=None
    ):
        rates_and_availability = helper.download_rates_and_availability(
            prop, checkin=checkin, checkout=checkout
        )
        if not rates_and_availability:
            return False

        availabilities_to_create = []
        availabilities_to_update = []

        for rate_data in rates_and_availability:
            room_type = RoomType.objects.filter(
                external_id=rate_data["room_type"]
            ).first()
            if not room_type:
                print(f"Room type not found: {rate_data['room_type']}")
                continue

            date_obj = datetime.strptime(rate_data["date"], "%Y-%m-%d").date()

            availability = Availability.objects.filter(
                property=prop,
                room_type=room_type,
                date=date_obj,
            ).first()

            rates_json = json.dumps(rate_data["rates"])
            availability_count = rate_data["availability"]

            if availability:
                if (
                    availability.rates == rates_json
                    and availability.availability == availability_count
                ):
                    continue
                availability.rates = rates_json
                availability.availability = availability_count
                availabilities_to_update.append(availability)
            else:
                availabilities_to_create.append(
                    Availability(
                        property=prop,
                        room_type=room_type,
                        date=date_obj,
                        rates=rates_json,
                        availability=availability_count,
                    )
                )

        if availabilities_to_update:
            Availability.objects.bulk_update(
                availabilities_to_update, ["rates", "availability"]
            )

        if availabilities_to_create:
            Availability.objects.bulk_create(
                availabilities_to_create,
                update_conflicts=True,
                unique_fields=["property", "room_type", "date"],
                update_fields=["rates", "availability"],
            )

        return True

    @classmethod
    def sync_property_detail(cls, prop: Property, helper):
        property_detail = helper.download_property_details(prop)
        if not property_detail:
            return False

        pms_data = prop.pms_data

        pms_data.pms_property_id = property_detail.get(
            "pms_property_id", pms_data.pms_property_id
        )
        pms_data.pms_property_name = property_detail.get(
            "pms_property_name", pms_data.pms_property_name
        )
        pms_data.pms_property_address = property_detail.get(
            "pms_property_address", pms_data.pms_property_address
        )
        pms_data.pms_property_city = property_detail.get(
            "pms_property_city", pms_data.pms_property_city
        )
        pms_data.pms_property_province = property_detail.get(
            "pms_property_province", pms_data.pms_property_province
        )
        pms_data.pms_property_postal_code = property_detail.get(
            "pms_property_postal_code", pms_data.pms_property_postal_code
        )
        pms_data.pms_property_country = property_detail.get(
            "pms_property_country", pms_data.pms_property_country
        )
        pms_data.pms_property_latitude = property_detail.get(
            "pms_property_latitude", pms_data.pms_property_latitude
        )
        pms_data.pms_property_longitude = property_detail.get(
            "pms_property_longitude", pms_data.pms_property_longitude
        )
        pms_data.pms_property_phone = property_detail.get(
            "pms_property_phone", pms_data.pms_property_phone
        )
        pms_data.pms_property_category = property_detail.get(
            "pms_property_category", pms_data.pms_property_category
        )
        pms_data.save()

        return True

    @classmethod
    def sync_rooms(cls, prop: Property, helper):
        rooms_grouped_by_type = helper.download_room_list(prop)
        if not rooms_grouped_by_type:
            return False

        # Aquí podrías guardar las habitaciones en la base de datos si es necesario
        for room_type_id in rooms_grouped_by_type:
            for room in rooms_grouped_by_type[room_type_id]:
                # Asegúrate de que room tenga los campos necesarios
                # if "taquilla" in room["external_room_type_name"].lower():
                #     continue
                room_type = RoomType.objects.filter(
                    property=prop,
                    external_id=room["external_room_type_id"],
                    name=room["external_room_type_name"],
                ).first()

                if not room_type:
                    room_type = RoomType.objects.create(
                        property=prop,
                        external_id=room["external_room_type_id"],
                        name=room["external_room_type_name"],
                    )

                pax = extract_pax(room["external_room_type_name"])
                Room.objects.update_or_create(
                    property=prop,
                    name=room["name"],
                    type=room_type,
                    external_id=room.get("external_id", ""),
                    external_room_type_id=room.get("external_room_type_id", ""),
                    external_room_type_name=room.get("external_room_type_name", ""),
                    pax=pax,
                    defaults={
                        "description": room.get("description", ""),
                    },
                )
        return True

    @classmethod
    def sync_reservations(cls, prop: Property, helper, user=None):
        reservations_data = helper.download_reservations(prop)
        if not reservations_data:
            return False

        reservations_to_create = []
        reservations_rooms_to_create = []
        for reservation_data in reservations_data:

            already_exist = Reservation.objects.filter(
                user=user if user else None,
                check_in=datetime.strptime(
                    reservation_data["check_in"], "%Y-%m-%d"
                ).date(),
                check_out=datetime.strptime(
                    reservation_data["check_out"], "%Y-%m-%d"
                ).date(),
                property_id=prop.id,
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
                user=user,
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

            if rooms := reservation_data["rooms"]:
                for room in rooms:

                    if not (
                        room_type := RoomType.objects.filter(
                            external_id=room["room_type_id"]
                        ).first()
                    ):
                        print(f"Room type not found: {room['room_type_id']}")
                        continue

                    reservation_room = ReservationRoom(
                        reservation=reservation,
                        room_type=room_type,
                        price=reservation_data.get("total_price", 0),
                        guests=room.get("occupancy", 1),
                    )
                    reservations_rooms_to_create.append(reservation_room)

        if reservations_to_create:
            Reservation.objects.bulk_create(reservations_to_create)

        if reservations_rooms_to_create:
            ReservationRoom.objects.bulk_create(reservations_rooms_to_create)

        return True
