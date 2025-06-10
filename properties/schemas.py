from datetime import date
from typing import List, Optional

from ninja import Schema

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
    rate_external_id: Optional[str] = None
    availability: int  # ForeignKey to Availability, represented as an int for simplicity
    prices: List[Price]
    restriction: Optional[dict] = None  # JSONField for restrictions


class AvailabilityOut(Schema):
    date: date
    availability: int
    rates: List[Rate]


class RoomTypeOut(Schema):
    id: int
    name: str
    external_id: str
    description: Optional[str] = None
    # availability: List[AvailabilityOut]


class RoomOut(Schema):
    id: int
    name: str
    description: str
    pax: int
    services: List[str]
    images: Optional[List[str]]
    property_id: int
    type: str

    @staticmethod
    def resolve_services(obj):
        return [service.name for service in obj.services.all()] if obj.services else []

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


class TermsAndConditionsOut(Schema):
    condition_of_confirmation: str
    check_in_time: str
    check_out_time: str
    cancellation_policy: str
    additional_information: str


class PropertyOut(Schema):
    id: int
    name: str
    zone: str
    zone_id: int
    description: str

    address: str

    # calculated fields
    cover_image: Optional[str]
    images: Optional[List[str]]
    room_types: Optional[List[RoomTypeOut]]
    communication_methods: Optional[List[str]]
    location: Optional[str]
    terms_and_conditions: Optional[TermsAndConditionsOut] = None

    @staticmethod
    def resolve_zone(obj):
        return obj.zone.name

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
    def resolve_location(obj):
        return obj.location.geojson if obj.location else None

    @staticmethod
    def resolve_terms_and_conditions(obj):
        if obj.terms_and_conditions:
            return obj.terms_and_conditions
        return None

    @staticmethod
    def resolve_room_types(obj):
        room_types = set()
        for room in obj.rooms.all():
            if room.type:
                room_types.add(room.type)
        return list(room_types) if room_types else None


