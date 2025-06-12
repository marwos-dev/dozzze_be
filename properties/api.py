import json
from datetime import timedelta
from typing import List, Optional

from django.conf import settings
from ninja import Query, Router
from ninja.errors import HttpError
from ninja.security import APIKeyHeader

from pms.utils.property_helper_factory import PMSHelperFactory

from .models import Availability, Property, Room
from .schemas import AvailabilityRequest, PropertyOut, RoomAvailability, RoomOut
from .sync_service import SyncService


class FrontendTokenAuth(APIKeyHeader):
    param_name = "X-API-KEY"  # o "Authorization"

    def authenticate(self, request, key):
        if key == settings.MY_FRONTEND_SECRET_TOKEN:
            return key
        raise HttpError(401, "Invalid API key")


router = Router(tags=["properties"])


@router.get("/", response={200: List[PropertyOut], 400: str})
def available_properties(
    request,
    zona: Optional[int] = Query(None),
):
    propiedades = Property.objects.filter(active=True)

    if zona:
        propiedades = propiedades.filter(zone_id=zona)
    return propiedades


@router.post("/availability/", response=List[RoomAvailability])
def get_availability(request, data: AvailabilityRequest):
    if not data.check_in:
        raise HttpError(403, "Invalid check-in date")

    if data.check_in > data.check_out:
        raise HttpError(403, "Check-in date cannot be after check-out date")

    property_obj = data.property_id
    if property_obj:
        property_obj = Property.objects.filter(id=data.property_id, active=True).first()
        if not property_obj:
            raise HttpError(404, "Property not found")

    helper = None
    if property_obj:
        helper = PMSHelperFactory().get_helper(property_obj)

    # Paso 1: Verificar si hay datos disponibles en base de datos
    existing_data = Availability.existing_for(
        data.check_in, data.check_out, property_obj, data.room_type
    )

    # Paso 2: Verificar si faltan fechas
    expected_dates = set(
        data.check_in + timedelta(days=i)
        for i in range((data.check_out - data.check_in).days)
    )
    existing_dates = set(a.date for a in existing_data)
    missing_dates = expected_dates - existing_dates

    if missing_dates or not existing_data:
        # Si faltan fechas, sincronizamos
        if property_obj and helper:
            SyncService.sync_rates_and_availability(
                property_obj, helper, checkin=data.check_in, checkout=data.check_out
            )
        # Vuelve a buscar con los datos frescos
        existing_data = Availability.existing_for(
            data.check_in, data.check_out, property_obj, room_type_id=data.room_type
        )

    # Paso 3: Armar la respuesta
    response = []
    for availability in existing_data:
        try:
            parsed_rates = json.loads(availability.rates)
        except Exception:
            raise HttpError(500, "Could not parse rates")

        response.append(
            RoomAvailability(
                date=availability.date,
                room_type=availability.room_type.name,
                availability=availability.availability,
                rates=parsed_rates,
                property_id=availability.property_id,
            )
        )

    return response


@router.get("/{property_id}", response=PropertyOut)
def get_property(request, property_id: int):
    try:
        _property = Property.objects.get(id=property_id)
        return _property
    except Property.DoesNotExist:
        return {"error": "Property not found"}


@router.get("/{property_id}/rooms", response=List[RoomOut])
def get_property_rooms(request, property_id: int):
    try:
        _property = Property.objects.get(id=property_id)
        return _property.rooms.all()
    except Property.DoesNotExist:
        raise HttpError(404, "Property not found")


@router.get("/rooms/{room_id}", response=RoomOut)
def get_room(request, room_id: int):
    try:
        room = Room.objects.get(id=room_id)
        return room
    except Room.DoesNotExist:
        raise HttpError(404, "Room not found")


@router.get("/rooms", response=List[RoomOut])
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
            raise HttpError(400, "Zone ID or Property ID is required")

        return Room.objects.filter(property__in=properties)
    except Property.DoesNotExist:
        raise HttpError(404, "Property not found")
