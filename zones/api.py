from typing import List

from ninja import Router
from ninja.responses import Response

from utils import APIError, ErrorSchema, ZoneErrorCode

from .models import Zone
from .schemas import ZoneOut

router = Router(tags=["zones"])


@router.get("/{zone_id}/polygon")
def zone_polygon(request, zone_id):
    zone_search = Zone.objects.filter(id=zone_id).first()
    if not zone_search:
        raise APIError("Zone not found", ZoneErrorCode.INVALID_ZONE_ID ,404)
    return Response(
        {
            "coordinates": zone_search.area.geojson,
            "name": zone_search.name,
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
    if not (zone_search := Zone.objects.filter(id=zone_id).first()):
        raise APIError("Zone not found", ZoneErrorCode.INVALID_ZONE_ID, 404)
    return zone_search
