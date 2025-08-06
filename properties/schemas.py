from datetime import date
from typing import List, Optional

from ninja import Field, Schema

from utils import generate_presigned_url


class PropertySearchInput(Schema):
    zona: int
    pax: int
    checkin: date
    checkout: date


class Price(Schema):
    price: float
    occupancy: int


class Rate(Schema):
    # rate_external_id: Optional[str] = None
    # availability: int  # ForeignKey to Availability, represented as an int for simplicity
    prices: List[Price]
    restriction: Optional[dict] = None  # JSONField for restrictions


class AvailabilityOut(Schema):
    date: date
    availability: int
    rates: List[Rate]


class ServiceIn(Schema):
    code: str
    name: str
    description: Optional[str] = None


class ServiceUpdateIn(ServiceIn):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class ServiceOut(ServiceIn):
    id: int


class RoomTypeOut(Schema):
    id: int
    name: str
    description: Optional[str] = None
    images: Optional[List[str]] = None
    services: Optional[List[ServiceOut]] = None

    @staticmethod
    def resolve_images(obj):
        return (
            [
                generate_presigned_url(room_type_image.image.name)
                for room_type_image in obj.images.all()
            ]
            if obj.images
            else []
        )

    @staticmethod
    def resolve_services(obj):
        if obj.property and obj.property.services.exists():
            return [
                ServiceOut(
                    id=service.id,
                    code=service.code,
                    name=service.name,
                    description=service.description,
                )
                for service in obj.property.services.all()
            ]
        return []


class RoomOut(Schema):
    id: int
    name: str
    description: str
    pax: int
    images: Optional[List[str]]
    property_id: int
    type: str

    @staticmethod
    def resolve_images(obj):
        return (
            [
                generate_presigned_url(room_image.image.name)
                for room_image in obj.images.all()
            ]
            if obj.images
            else []
        )

    @staticmethod
    def resolve_type(obj):
        return obj.type.name if obj.type else None


class TermsAndConditionsOut(Schema):
    condition_of_confirmation: str
    check_in_time: str
    check_out_time: str
    cancellation_policy: str
    additional_information: str


class PropertyOut(Schema):
    id: int
    name: str
    zone: Optional[str] = None
    zone_id: Optional[int] = None
    description: str

    address: str

    # calculated fields
    cover_image: Optional[str]
    images: Optional[List[str]]
    room_types: Optional[List[RoomTypeOut]]
    communication_methods: Optional[List[str]]
    location: Optional[str]
    terms_and_conditions: Optional[TermsAndConditionsOut] = None
    services: Optional[List[ServiceOut]] = None

    @staticmethod
    def resolve_zone(obj):
        return obj.zone.name if obj.zone else None

    @staticmethod
    def resolve_images(obj):
        return (
            [
                generate_presigned_url(zone_image.image.name)
                for zone_image in obj.gallery.all()
            ]
            if obj.gallery
            else []
        )

    @staticmethod
    def resolve_cover_image(obj):
        return generate_presigned_url(obj.cover_image.name) if obj.cover_image else None

    @staticmethod
    def resolve_communication_methods(obj):
        return (
            [method.name for method in obj.communication_methods.all()]
            if obj.communication_methods
            else []
        )

    @staticmethod
    def resolve_services(obj):
        if obj.services.exists():
            return [
                ServiceOut(
                    id=service.id,
                    code=service.code,
                    name=service.name,
                    description=service.description,
                )
                for service in obj.services.all()
            ]
        return []

    @staticmethod
    def resolve_location(obj):
        return obj.location.geojson if obj.location else None

    @staticmethod
    def resolve_terms_and_conditions(obj):
        if obj.terms_and_conditions:
            return obj.terms_and_conditions
        return None

    @staticmethod
    def resolve_room_types(obj):
        return obj.room_types.all()


class RoomAvailability(Schema):
    date: date
    room_type: str
    room_type_id: int
    availability: int
    rates: List[Rate]
    property_id: int
    total_price: Optional[float] = None


class AvailabilityRequest(Schema):
    property_id: Optional[int] = Field(default=None)
    check_in: date
    check_out: date
    guests: Optional[int] = Field(default=2)
    room_type: Optional[int] = Field(default=None)


class AvailabilityResponse(Schema):
    rooms: List[RoomAvailability]
    total_price_per_room_type: Optional[dict] = None


class PropertyIn(Schema):
    name: str
    description: str
    address: str
    latitude: float
    longitude: float
    zone_id: Optional[int] = None
    pms_id: Optional[int] = None
    use_pms_information: Optional[bool] = False


class PropertyUpdateIn(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_id: Optional[int] = None
    pms_id: Optional[int] = None
    use_pms_information: Optional[bool] = None


class RoomTypeUpdateIn(Schema):
    """Input schema for updating a room type."""

    name: Optional[str] = None
    description: Optional[str] = None


class PropertyImageOut(Schema):
    id: int
    image: str
    caption: Optional[str] = None

    @staticmethod
    def resolve_image(obj):
        return generate_presigned_url(obj.image.name)


class RoomTypeImageOut(Schema):
    id: int
    image: str

    @staticmethod
    def resolve_image(obj):
        return generate_presigned_url(obj.image.name)


class PmsDataPropertyIn(Schema):
    base_url: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    pms_token: Optional[str] = None
    pms_hotel_identifier: Optional[str] = None
    pms_username: Optional[str] = None
    pms_password: Optional[str] = None
    pms_property_id: Optional[int] = None
    pms_property_name: Optional[str] = None
    pms_property_address: Optional[str] = None
    pms_property_city: Optional[str] = None
    pms_property_province: Optional[str] = None
    pms_property_postal_code: Optional[str] = None
    pms_property_country: Optional[str] = None
    pms_property_latitude: Optional[float] = None
    pms_property_longitude: Optional[float] = None
    pms_property_phone: Optional[str] = None
    pms_property_category: Optional[str] = None
    first_sync: Optional[bool] = None


class PmsDataPropertyOut(PmsDataPropertyIn):
    id: int
