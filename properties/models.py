from django.contrib.gis.db import models as geomodels
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage


class Service(models.Model):
    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["name"]
        unique_together = ("name",)

    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")

    def __str__(self):
        return self.name


class Property(models.Model):
    class Meta:
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"
        ordering = ["-created_at"]
        unique_together = ("name", "address")


    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripcion")
    address = models.CharField(max_length=255, verbose_name="Dirección")
    location = geomodels.PointField(geography=True, verbose_name="Ubicación")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    cover_image = models.ImageField(upload_to='properties/covers/', null=True, blank=True, verbose_name="Imagen",
                                    storage=S3Boto3Storage())
    zone = models.ForeignKey(
        'zones.Zone', related_name='properties', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Zona"
    )

    def __str__(self):
        return self.name


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name='gallery', on_delete=models.CASCADE, verbose_name="Zona")
    image = models.ImageField(upload_to='properties/gallery/', verbose_name="Imagen", storage=S3Boto3Storage())
    caption = models.CharField(max_length=255, blank=True, verbose_name="Descripción")

    def __str__(self):
        return f"Image of {self.property.name}"


class Room(models.Model):
    APARTMENT = "apartment"
    STUDIO = "studio"
    DUPLEX = "duplex"

    ROOM_TYPES = [
        (APARTMENT, "Apartment"),
        (STUDIO, "Studio"),
        (DUPLEX, "Duplex"),
    ]

    property = models.ForeignKey(Property, related_name="rooms", on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=ROOM_TYPES, verbose_name="Tipo")
    name = models.CharField(max_length=255)
    description = models.TextField()
    pax = models.PositiveIntegerField()
    services = models.ManyToManyField(Service, blank=True)


    def __str__(self):
        return f"{self.name} - {self.property.name}"

    class Meta:
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"
        ordering = ["name"]
        unique_together = ("name", "property")

    def is_available(self, check_in, check_out):
        return not self.reservations.filter(
            check_in__lt=check_out,
            check_out__gt=check_in
        ).exists()


def room_image_upload_path(instance, filename):
    return f"properties/{instance.room.property.id}/rooms/{instance.room.id}/{filename}"


class RoomImage(models.Model):
    room = models.ForeignKey(Room, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=room_image_upload_path)


class CommunicationMethod(models.Model):
    property = models.ForeignKey(Property, related_name="communication_methods", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    def __str__(self):
        return self.name
