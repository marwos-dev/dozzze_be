from datetime import date
from typing import List, Optional
from utils.s3_utils import generate_presigned_url

from ninja import Schema


class PropertySearchInput(Schema):
    zona: int
    pax: int
    checkin: date
    checkout: date


class RoomOut(Schema):
    id: int
    name: str
    description: str
    pax: int
    services: List[str]
    images: Optional[List[str]]

    @staticmethod
    def resolve_services(obj):
        return [service.name for service in obj.services.all()] if obj.services else []

    @staticmethod
    def resolve_images(obj):
        return [generate_presigned_url(room_image.image.name) for room_image in obj.images.all()] if obj.images else []


class PropertyOut(Schema):
    id: int
    name: str
    zone: str
    description: str

    address: str

    # calculated fields
    cover_image: Optional[str]
    images: Optional[List[str]]
    rooms: Optional[List[RoomOut]]
    communication_methods: Optional[List[str]]
    location: Optional[str]

    @staticmethod
    def resolve_zone(obj):
        return obj.zone.name

    @staticmethod
    def resolve_images(obj):
        return [generate_presigned_url(zone_image.image.name) for zone_image in obj.gallery.all()] if obj.gallery else []

    @staticmethod
    def resolve_cover_image(obj):
        return obj.cover_image.url if obj.cover_image else None

    @staticmethod
    def resolve_rooms(obj):
        return obj.rooms.all() if obj.rooms else None

    @staticmethod
    def resolve_communication_methods(obj):
        return [method.name for method in obj.communication_methods.all()] if obj.communication_methods else []

    @staticmethod
    def resolve_location(obj):
        return obj.location.geojson if obj.location else None
