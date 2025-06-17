from typing import List

from ninja import Router
from ninja.errors import HttpError
from ninja.responses import Response

from utils import ErrorSchema
from .models import Zone
from .schemas import ZoneOut

router = Router(tags=["zones"])


@router.get("/{zone_id}/polygon")
def zone_polygon(request, zone_id):
    zone = Zone.objects.get(id=zone_id)
    return Response(
        {
            "coordinates": zone.area.geojson,
            "name": zone.name,
        }
    )


@router.get("/", response={200: List[ZoneOut]})
def zones(request):
    """
    This endpoint fetches all zones.

    Response codes:
    * 200 OK - Returns a list of zones
    * 400 Bad Request - Error fetching zones
    """
    return Zone.objects.all()


@router.get("/{zone_id}/", response={200: ZoneOut, 404: ErrorSchema})
def zone(request, zone_id):
    """
    This endpoint fetches a zone by ID.

    Response codes:
    * 200 OK - Returns the zone details
    * 404 Not Found - Zone not found
    """
    try:
        return Zone.objects.get(id=zone_id)
    except Zone.DoesNotExist:
        raise HttpError(404, "Zone not found")