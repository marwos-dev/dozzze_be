from typing import List, Optional

from django.conf import settings
from ninja import Query, Router
from ninja.errors import HttpError
from ninja.security import APIKeyHeader

from .models import Property, Room
from .schemas import PropertyOut, RoomOut


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
