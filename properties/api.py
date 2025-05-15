from ninja import Router, Query
from typing import Optional, List
from datetime import date

from ninja.errors import HttpError

from .models import Property
from .schemas import PropertyOut
from django.conf import settings
from ninja.security import APIKeyHeader

class FrontendTokenAuth(APIKeyHeader):
    param_name = "X-API-KEY"  # o "Authorization"

    def authenticate(self, request, key):
        if key == settings.MY_FRONTEND_SECRET_TOKEN:
            return key
        raise HttpError(401, "Invalid API key")


router = Router(tags=["properties"])


@router.get("/", response={200:List[PropertyOut], 400:str})
def available_properties(
    request,
    zona: Optional[int] = Query(None),
):
    # today = date.today()

    # Validaciones de fechas
    # if checkin and checkin < today:
    #     raise HttpError(400, "La fecha de check-in no puede ser anterior a hoy.")
    #
    # if checkout and checkout < today:
    #     raise HttpError(400, "La fecha de check-out no puede ser anterior a hoy.")
    #
    # if checkin and checkout and checkout <= checkin:
    #     raise HttpError(400, "La fecha de check-out debe ser posterior a la de check-in.")

    propiedades = Property.objects.filter(active=True)

    if zona:
        propiedades = propiedades.filter(zone_id=zona)

    # if pax:
    #     propiedades = propiedades.filter(pax__gte=pax)

    # # Verificamos si se puede hacer el filtro por fechas
    # if checkin:
    #     propiedades = propiedades.exclude(
    #         reservations__check_out__gt=checkin
    #     )
    #
    # if checkout:
    #     propiedades = propiedades.exclude(
    #         reservations__check_in__lt=checkout
    #     )

    return propiedades


@router.get("/{property_id}", response=PropertyOut)
def get_property(request, property_id: int):
    try:
        _property = Property.objects.get(id=property_id)
        return _property
    except Property.DoesNotExist:
        return {"error": "Property not found"}
