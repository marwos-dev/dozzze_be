"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from customers.api import customer_router
from properties.api import router as properties_router
from reservations.api import router as reservation_router
from pms.api import router as pms_router
from utils.auth_bearer import AuthBearer
from utils.error_codes import APIError
from utils.schemas import ErrorSchema
from utils.security import PublicAPIKey
from zones.api import router as zones_router

public_auth = PublicAPIKey()
auth_bearer = AuthBearer()


def api_exception_handler(request, exc: APIError):
    return api.create_response(
        request,
        ErrorSchema(detail=str(exc.message), code=int(exc.code)),
        status=exc.status_code,
    )


api = NinjaAPI()
api.add_exception_handler(APIError, api_exception_handler)

api.add_router(
    "/customers/",
    customer_router,
    auth=auth_bearer,
)
api.add_router(
    "/properties/",
    properties_router,
    auth=public_auth,
)
api.add_router(
    "/zones/",
    zones_router,
    auth=public_auth,
)

api.add_router(
    "/reservations/",
    reservation_router,
    auth=auth_bearer,
)
api.add_router(
    "/pms/",
    pms_router,
    auth=public_auth,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
