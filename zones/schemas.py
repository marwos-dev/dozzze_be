from typing import List, Optional

from ninja import Schema

from properties.schemas import PropertyOut


class ZoneOut(Schema):
    id: int
    name: str
    description: Optional[str] = None
    area: Optional[str] = None
    cover_image: Optional[str] = None
    images: Optional[List[str]] = None
    properties: List[PropertyOut] = []

    @staticmethod
    def resolve_area(obj):
        return obj.area.geojson if obj.area else None

    @staticmethod
    def resolve_images(obj):
        return [image.image.url for image in obj.gallery.all()] if obj.gallery else []

    @staticmethod
    def resolve_cover_image(obj):
        return obj.cover_image.image.url if obj.cover_image else None

    @staticmethod
    def resolve_properties(obj):
        return obj.properties.all() if obj.properties else []
