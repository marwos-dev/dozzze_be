from typing import List, Optional

from ninja import File, Form, Query, Router
from ninja.files import UploadedFile
from ninja.throttling import UserRateThrottle

from utils import APIError, ErrorSchema, PropertyErrorCode, SecurityErrorCode, SuccessSchema
from utils.auth_bearer import AuthBearer

from .models import Property, Room
from .schemas import (
    AvailabilityRequest,
    AvailabilityResponse,
    PmsDataPropertyIn,
    PmsDataPropertyOut,
    PropertyImageOut,
    PropertyIn,
    PropertyOut,
    PropertyUpdateIn,
    RoomAvailability,
    RoomOut,
    RoomTypeImageOut,
)
from .services import PropertyService

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
    return PropertyService.available_properties(zona)


@router.post(
    "/availability/",
    response={200: AvailabilityResponse, 404: ErrorSchema},
    # throttle=[UserRateThrottle("10/m")],
)
def get_availability(request, data: AvailabilityRequest):
    return PropertyService.get_availability(data)


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


# ----------------------- Staff management endpoints -----------------------


@router.get("/my/", response=List[PropertyOut], auth=AuthBearer())
def my_properties(request):
    if not request.user.is_staff:
        raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
    return Property.objects.filter(owner=request.user)


@router.post("/my/", response=PropertyOut, auth=AuthBearer())
def create_property(request, data: PropertyIn):
    return PropertyService.create_property(request.user, data)


@router.put("/my/{property_id}", response=PropertyOut, auth=AuthBearer())
def update_property(request, property_id: int, data: PropertyUpdateIn):
    return PropertyService.update_property(request.user, property_id, data)


@router.delete(
    "/my/{property_id}",
    response={200: SuccessSchema, 404: ErrorSchema},
    auth=AuthBearer(),
)
def delete_property(request, property_id: int):
    return PropertyService.delete_property(request.user, property_id)


@router.get(
    "/my/{property_id}/pms-data",
    response={200: PmsDataPropertyOut, 404: ErrorSchema},
    auth=AuthBearer(),
)
def get_pms_data(request, property_id: int):
    return PropertyService.get_pms_data(request.user, property_id)


@router.post(
    "/my/{property_id}/pms-data", response=PmsDataPropertyOut, auth=AuthBearer()
)
def create_pms_data(request, property_id: int, data: PmsDataPropertyIn):
    return PropertyService.create_pms_data(request.user, property_id, data)


@router.put(
    "/my/{property_id}/pms-data", response=PmsDataPropertyOut, auth=AuthBearer()
)
def update_pms_data(request, property_id: int, data: PmsDataPropertyIn):
    return PropertyService.update_pms_data(request.user, property_id, data)


@router.get(
    "/my/{property_id}/images", response=List[PropertyImageOut], auth=AuthBearer()
)
def list_property_images(request, property_id: int):
    return PropertyService.list_property_images(request.user, property_id)


@router.post("/my/{property_id}/images", response=PropertyImageOut, auth=AuthBearer())
def add_property_image(
    request,
    property_id: int,
    image: UploadedFile = File(...),
    caption: str = Form(None),
):
    return PropertyService.add_property_image(request.user, property_id, image, caption)


@router.delete(
    "/my/{property_id}/images/{image_id}",
    response={200: SuccessSchema, 404: ErrorSchema},
    auth=AuthBearer(),
)
def delete_property_image(request, property_id: int, image_id: int):
    return PropertyService.delete_property_image(request.user, property_id, image_id)


@router.get(
    "/my/room-types/{room_type_id}/images",
    response=List[RoomTypeImageOut],
    auth=AuthBearer(),
)
def list_room_type_images(request, room_type_id: int):
    return PropertyService.list_room_type_images(request.user, room_type_id)


@router.post(
    "/my/room-types/{room_type_id}/images", response=RoomTypeImageOut, auth=AuthBearer()
)
def add_room_type_image(request, room_type_id: int, image: UploadedFile = File(...)):
    return PropertyService.add_room_type_image(request.user, room_type_id, image)


@router.post(
    "/my/{property_id}/sync",
    response={200: SuccessSchema, 404: ErrorSchema},
    auth=AuthBearer(),
)
def sync_property_with_pms(request, property_id: int):
    """Synchronize a property with its PMS."""
    return PropertyService.sync_property_with_pms(request.user, property_id)
