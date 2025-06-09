from typing import List, Optional

from ninja import Schema

from properties.schemas import PropertyOut
from utils import generate_presigned_url


class ZoneOut(Schema):
    id: int
    name: str
    description: Optional[str] = None
    area: Optional[str] = None
    cover_image: Optional[str] = None
    images: Optional[List[str]] = []
    properties: List[PropertyOut] = []

    @staticmethod
    def resolve_area(obj):
        return obj.area.geojson if obj.area else None

    @staticmethod
    def resolve_images(obj):
        return (
            [
                generate_presigned_url(image.image.name)
                for image in obj.zone_images.all()
            ]
            if obj.zone_images
            else []
        )

    @staticmethod
    def resolve_cover_image(obj):
        return (
            generate_presigned_url(obj.cover_image.image.name)
            if obj.cover_image
            else None
        )

    @staticmethod
    def resolve_properties(obj):
        return obj.properties.all() if obj.properties else []
