import json
from collections import defaultdict
from datetime import timedelta
from typing import List, Optional

from ninja import Query, Router
from ninja.throttling import UserRateThrottle

from pms.utils.property_helper_factory import PMSHelperFactory
from utils import APIError, ErrorSchema, PropertyErrorCode

from .models import Availability, Property, Room
from .schemas import (
    AvailabilityRequest,
    AvailabilityResponse,
    PropertyOut,
    RoomAvailability,
    RoomOut,
)
from .sync_service import SyncService

router = Router(tags=["properties"])


@router.get(
    "/",
    response={200: List[PropertyOut], 400: str},
    throttle=[UserRateThrottle("10/m")],
)
def available_properties(
    request,
    zona: Optional[int] = Query(None),
):
    propiedades = Property.objects.filter(active=True)

    if zona:
        propiedades = propiedades.filter(zone_id=zona)
    return propiedades


@router.post(
    "/availability/",
    response={200: AvailabilityResponse, 404: ErrorSchema},
    # throttle=[UserRateThrottle("10/m")],
)
def get_availability(request, data: AvailabilityRequest):
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
        property_obj = Property.objects.filter(id=data.property_id, active=True).first()
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
    existing_dates = set(a.date for a in existing_data)
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

    rooms_availability = []
    total_price_per_room_type = {}

    for room_type_name, availabilities in grouped_by_room_type.items():
        availability_by_date = {a.date: a for a in availabilities}
        if not all(
            d in availability_by_date and availability_by_date[d].availability > 0
            for d in date_range
        ):
            continue  # alguna fecha no tiene disponibilidad

        rate_totals = defaultdict(float)
        rate_valid = defaultdict(lambda: True)
        rates_cache_by_date = {}

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
                    rates=parsed_rates,  # solo para visual
                    property_id=availability.property_id,
                )
            )

            rates_cache_by_date[date] = parsed_rates  # solo para mostrar una en rooms

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

        # Filtrar solo los válidos
        valid_totals = [
            {"rate_index": i, "total_price": round(rate_totals[i], 2)}
            for i in rate_totals
            if rate_valid[i]
        ]

        if not valid_totals:
            continue

        # Agregar una sola room para mostrar

        total_price_per_room_type[f"{room_type_name}-guests:{data.guests}"] = (
            valid_totals
        )

    if not rooms_availability:
        raise APIError(
            "No availability for the selected dates",
            PropertyErrorCode.NO_AVAILABILITY,
            404,
        )

    return {
        "rooms": rooms_availability,
        "total_price_per_room_type": total_price_per_room_type,
    }


@router.get("/{property_id}", response=PropertyOut, throttle=[UserRateThrottle("1/m")])
def get_property(request, property_id: int):
    try:
        _property = Property.objects.get(id=property_id)
        return _property
    except Property.DoesNotExist:
        raise APIError("Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404)


@router.get(
    "/{property_id}/rooms", response=List[RoomOut], throttle=[UserRateThrottle("10/m")]
)
def get_property_rooms(request, property_id: int):
    try:
        _property = Property.objects.get(id=property_id)
        return _property.rooms.all()
    except Property.DoesNotExist:
        raise APIError("Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404)


@router.get("/rooms/{room_id}", response=RoomOut, throttle=[UserRateThrottle("10/m")])
def get_room(request, room_id: int):
    try:
        room = Room.objects.get(id=room_id)
        return room
    except Room.DoesNotExist:
        raise APIError("Room not found", PropertyErrorCode.ROOM_NOT_FOUND, 404)


@router.get("/rooms", response=List[RoomOut], throttle=[UserRateThrottle("10/m")])
def get_rooms(
    request,
    zone_id: Optional[int] = Query(),
    property_id: Optional[int] = Query(None),
):
    try:
        if zone_id:
            properties = Property.objects.filter(zone_id=zone_id)
        elif property_id:
            properties = Property.objects.filter(id=property_id)
        else:
            raise APIError(
                "Zone ID or Property ID is required",
                PropertyErrorCode.ZONE_OR_PROPERTY_REQUIRED,
                400,
            )

        return Room.objects.filter(property__in=properties)
    except Property.DoesNotExist:
        raise APIError("Property not found", PropertyErrorCode.PROPERTY_NOT_FOUND, 404)
