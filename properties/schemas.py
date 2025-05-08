from ninja import Schema
from datetime import date

class PropertySearchInput(Schema):
    zona: int
    pax: int
    checkin: date
    checkout: date

class PropertyOut(Schema):
    id: int
    name: str
    pax: int
    zone: str

    @staticmethod
    def resolve_zone(obj):
        return obj.zone.name

