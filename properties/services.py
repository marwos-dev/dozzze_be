# New service file for property related operations
import json
from collections import defaultdict
from datetime import timedelta
from typing import List, Optional

from django.contrib.gis.geos import Point
from django.utils.text import slugify

from pms.models import PMS
from pms.utils.property_helper_factory import PMSHelperFactory
from utils import (
    APIError,
    PropertyErrorCode,
    SecurityErrorCode,
    SuccessSchema,
    ZoneErrorCode,
)
from zones.models import Zone

from .models import (
    Availability,
    PmsDataProperty,
    Property,
    PropertyImage,
    RoomType,
    RoomTypeImage,
)
from .schemas import (
    AvailabilityRequest,
    AvailabilityResponse,
    PmsDataPropertyIn,
    PropertyIn,
    PropertyUpdateIn,
    RoomAvailability,
    RoomTypeUpdateIn,
)
from .sync_service import SyncService


class PropertyService:
    """Service layer for property operations."""

    @staticmethod
    def available_properties(zona: Optional[int]) -> List[Property]:
        propiedades = Property.objects.filter(active=True)
        if zona:
            propiedades = propiedades.filter(zone_id=zona)
        return list(propiedades)

    @staticmethod
    def get_property_by_name(name: str) -> Property:
        """Retrieve a property by slugified name."""
        for prop in Property.objects.filter(active=True):
            if slugify(prop.name) == slugify(name):
                return prop
        raise APIError(
            "Property not found",
            PropertyErrorCode.PROPERTY_NOT_FOUND,
            404,
        )

    @staticmethod
    def get_availability(data: AvailabilityRequest) -> AvailabilityResponse:
        if not data.check_in:
            raise APIError(
                "Invalid check-in date", PropertyErrorCode.INVALID_CHECKIN_DATE, 403
            )

        if data.check_in > data.check_out:
            raise APIError(
                "Check-in date cannot be after check-out date",
                PropertyErrorCode.CHECKIN_AFTER_CHECKOUT,
                403,
            )

        property_obj = None
        if data.property_id:
            property_obj = Property.objects.filter(
                id=data.property_id, active=True
            ).first()
            if not property_obj:
                raise APIError(
                    "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
                )

        date_range = [
            data.check_in + timedelta(days=i)
            for i in range((data.check_out - data.check_in).days)
        ]

        existing_data = Availability.existing_for(
            data.check_in, data.check_out, property_obj, data.room_type
        )
        existing_dates = {a.date for a in existing_data}
        missing_dates = set(date_range) - existing_dates

        if not existing_data or missing_dates:
            if property_obj:
                helper = PMSHelperFactory().get_helper(property_obj)
                SyncService.sync_rates_and_availability(
                    property_obj, helper, checkin=data.check_in, checkout=data.check_out
                )
            else:
                for prop in Property.objects.filter(active=True):
                    helper = PMSHelperFactory().get_helper(prop)
                    SyncService.sync_rates_and_availability(
                        prop, helper, checkin=data.check_in, checkout=data.check_out
                    )

            existing_data = Availability.existing_for(
                data.check_in, data.check_out, property_obj, room_type_id=data.room_type
            )

        grouped_by_room_type = defaultdict(list)
        for availability in existing_data:
            grouped_by_room_type[availability.room_type.name].append(availability)

        rooms_availability: List[RoomAvailability] = []
        total_price_per_room_type = {}

        for room_type_name, availabilities in grouped_by_room_type.items():
            availability_by_date = {a.date: a for a in availabilities}
            if not all(
                d in availability_by_date and availability_by_date[d].availability > 0
                for d in date_range
            ):
                continue

            rate_totals = defaultdict(float)
            rate_valid = defaultdict(lambda: True)

            for date in date_range:
                availability = availability_by_date[date]
                try:
                    parsed_rates = json.loads(availability.rates)
                except Exception:
                    raise APIError(
                        f"Could not parse rates for date {date}",
                        PropertyErrorCode.RATES_PARSE_ERROR,
                        400,
                    )

                rooms_availability.append(
                    RoomAvailability(
                        date=availability.date,
                        room_type=room_type_name,
                        room_type_id=availability.room_type_id,
                        availability=availability.availability,
                        rates=parsed_rates,
                        property_id=availability.property_id,
                    )
                )

                for i, rate in enumerate(parsed_rates):
                    found = False
                    for price in rate.get("prices", []):
                        if price.get("occupancy") == data.guests:
                            rate_totals[i] += price["price"]
                            found = True
                            break
                    if not found:
                        raise APIError(
                            f"No price found for {data.guests} guests",
                            PropertyErrorCode.PRICE_NOT_FOUND,
                            400,
                        )

            valid_totals = [
                {"rate_index": i, "total_price": round(rate_totals[i], 2)}
                for i in rate_totals
                if rate_valid[i]
            ]

            if not valid_totals:
                continue

            total_price_per_room_type[f"{room_type_name}-guests:{data.guests}"] = (
                valid_totals
            )

        if not rooms_availability:
            raise APIError(
                "No availability for the selected dates",
                PropertyErrorCode.NO_AVAILABILITY,
                404,
            )

        return AvailabilityResponse(
            rooms=rooms_availability,
            total_price_per_room_type=total_price_per_room_type,
        )

    @staticmethod
    def create_property(user, data: PropertyIn) -> Property:
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        zone = None
        if data.zone_id is not None:
            zone = Zone.objects.filter(id=data.zone_id).first()
            if not zone:
                raise APIError("Zone not found", ZoneErrorCode.INVALID_ZONE_ID, 404)

        pms = None
        if data.pms_id is not None:
            pms = PMS.objects.filter(id=data.pms_id).first()
            if not pms:
                raise APIError(
                    "PMS not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
                )

        if Property.objects.filter(
            owner=user, name=data.name, address=data.address
        ).exists():
            raise APIError(
                "Property already exists", PropertyErrorCode.PROPERTY_NOT_FOUND, 400
            )

        prop = Property.objects.create(
            owner=user,
            name=data.name,
            description=data.description,
            address=data.address,
            location=Point(data.longitude, data.latitude),
            zone=zone,
            pms=pms,
            use_pms_information=data.use_pms_information,
        )
        return prop

    @staticmethod
    def update_property(user, property_id: int, data: PropertyUpdateIn) -> Property:
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )

        payload = data.dict(exclude_unset=True)

        if "zone_id" in payload:
            zone = Zone.objects.filter(id=payload.pop("zone_id")).first()
            if not zone:
                raise APIError("Zone not found", ZoneErrorCode.INVALID_ZONE_ID, 404)
            prop.zone = zone

        if "pms_id" in payload:
            pms = PMS.objects.filter(id=payload.pop("pms_id")).first()
            if not pms:
                raise APIError(
                    "PMS not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
                )
            prop.pms = pms

        new_name = payload.get("name", prop.name)
        new_addr = payload.get("address", prop.address)
        if (
            Property.objects.filter(owner=user, name=new_name, address=new_addr)
            .exclude(id=prop.id)
            .exists()
        ):
            raise APIError(
                "Property already exists", PropertyErrorCode.PROPERTY_NOT_FOUND, 400
            )

        lat = payload.pop("latitude", None)
        lon = payload.pop("longitude", None)
        for attr, value in payload.items():
            setattr(prop, attr, value)
        if lat is not None and lon is not None:
            prop.location = Point(lon, lat)
        prop.save()
        return prop

    @staticmethod
    def delete_property(user, property_id: int) -> SuccessSchema:
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        prop.delete()
        return SuccessSchema(message="Property deleted")

    @staticmethod
    def get_pms_data(user, property_id: int):
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        try:
            return prop.pms_data
        except PmsDataProperty.DoesNotExist:
            raise APIError(
                "PMS data not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )

    @staticmethod
    def create_pms_data(user, property_id: int, data: PmsDataPropertyIn):
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        pms_data, _ = PmsDataProperty.objects.get_or_create(property=prop)
        for attr, value in data.dict(exclude_unset=True).items():
            setattr(pms_data, attr, value)
        pms_data.save()
        return pms_data

    @staticmethod
    def update_pms_data(user, property_id: int, data: PmsDataPropertyIn):
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        try:
            pms_data = prop.pms_data
        except PmsDataProperty.DoesNotExist:
            raise APIError(
                "PMS data not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        for attr, value in data.dict(exclude_unset=True).items():
            setattr(pms_data, attr, value)
        pms_data.save()
        return pms_data

    @staticmethod
    def list_property_images(user, property_id: int) -> List[PropertyImage]:
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        return list(prop.gallery.all())

    @staticmethod
    def add_property_image(user, property_id: int, image, caption: str | None):
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        img = PropertyImage.objects.create(
            property=prop, image=image, caption=caption or ""
        )
        return img

    @staticmethod
    def delete_property_image(user, property_id: int, image_id: int) -> SuccessSchema:
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )
        try:
            img = PropertyImage.objects.get(id=image_id, property=prop)
        except PropertyImage.DoesNotExist:
            raise APIError("Image not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404)
        img.delete()
        return SuccessSchema(message="Image deleted")

    @staticmethod
    def list_room_type_images(user, room_type_id: int) -> List[RoomTypeImage]:
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        rt = RoomType.objects.filter(id=room_type_id, property__owner=user).first()
        if not rt:
            raise APIError("Room not found", PropertyErrorCode.ROOM_NOT_FOUND, 404)
        return list(rt.images.all())

    @staticmethod
    def add_room_type_image(user, room_type_id: int, image):
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
        rt = RoomType.objects.filter(id=room_type_id, property__owner=user).first()
        if not rt:
            raise APIError("Room not found", PropertyErrorCode.ROOM_NOT_FOUND, 404)
        img = RoomTypeImage.objects.create(room_type=rt, image=image)
        return img

    @staticmethod
    def update_room_type(user, room_type_id: int, data: RoomTypeUpdateIn) -> RoomType:
        """Update a room type owned by the user."""
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)

        rt = RoomType.objects.filter(id=room_type_id, property__owner=user).first()
        if not rt:
            raise APIError("Room not found", PropertyErrorCode.ROOM_NOT_FOUND, 404)

        payload = data.dict(exclude_unset=True)
        for attr, value in payload.items():
            setattr(rt, attr, value)
        rt.save()
        return rt

    @staticmethod
    def sync_property_with_pms(user, property_id: int) -> SuccessSchema:
        if not user.is_staff:
            raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)

        prop = Property.objects.filter(id=property_id, owner=user).first()
        if not prop:
            raise APIError(
                "Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )

        try:
            helper = PMSHelperFactory().get_helper(prop)
        except Exception:
            raise APIError(
                "PMS helper not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404
            )

        SyncService.sync_property_detail(prop, helper)
        SyncService.sync_rooms(prop, helper)
        SyncService.sync_reservations(prop, helper, user)
        SyncService.sync_rates_and_availability(prop, helper)

        try:
            pms_data = prop.pms_data
        except PmsDataProperty.DoesNotExist:
            pms_data = None

        if pms_data and pms_data.first_sync:
            pms_data.first_sync = False
            pms_data.save()

        return SuccessSchema(message="Synchronization completed")
