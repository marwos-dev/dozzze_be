from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from properties.models import Property, Service, PropertyService
from zones.models import Zone


class Command(BaseCommand):
    help = "Create sample data for development environment"

    def handle(self, *args, **options):
        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com"},
        )
        zone, _ = Zone.objects.get_or_create(
            name="Zona Demo",
            defaults={"description": "Zona de ejemplo"},
        )
        wifi, _ = Service.objects.get_or_create(
            code="wifi",
            defaults={"name": "Wifi"},
        )
        prop, _ = Property.objects.get_or_create(
            owner=admin,
            name="Propiedad Demo",
            defaults={
                "description": "Propiedad de ejemplo",
                "address": "Calle Falsa 123",
                "location": Point(0, 0),
                "zone": zone,
            },
        )
        PropertyService.objects.get_or_create(property=prop, service=wifi)
        self.stdout.write(self.style.SUCCESS("Datos de ejemplo creados."))
