from typing import List

from ninja import Router

from .models import PMS
from .schemas import PMSOut

router = Router(tags=["pms"])


@router.get("/", response={200: List[PMSOut]})
def list_pms(request):
    """Return all PMS with integration enabled"""
    return list(PMS.objects.filter(active=True, has_integration=True))
