from django.contrib.gis.db import models as geomodels
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage
from uuid import uuid4


class Service(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")

    class Meta:
        db_table = "services"
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["name"]
        unique_together = ("name",)

    def __str__(self):
        return self.name


def property_cover_image_upload_path(instance, filename):
    return f"properties/cover_image/{filename}"


class Property(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripcion")
    address = models.CharField(max_length=255, verbose_name="Dirección")
    location = geomodels.PointField(geography=True, verbose_name="Ubicación")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    cover_image = models.ImageField(upload_to=property_cover_image_upload_path, null=True, blank=True,
                                    verbose_name="Imagen",
                                    storage=S3Boto3Storage())
    zone = models.ForeignKey(
        'zones.Zone', related_name='properties', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Zona"
    )

    class Meta:
        db_table = "properties"
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"
        ordering = ["-created_at"]
        unique_together = ("name", "address")

    def __str__(self):
        return self.name


def property_image_upload_path(instance, filename):
    return f"properties/gallery/{filename}"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name='gallery', on_delete=models.CASCADE, verbose_name="Zona")
    image = models.ImageField(upload_to=property_image_upload_path, verbose_name="Imagen", storage=S3Boto3Storage())
    caption = models.CharField(max_length=255, blank=True, verbose_name="Descripción")

    class Meta:
        db_table = "property_images"
        verbose_name = "Imagen de Propiedad"
        verbose_name_plural = "Imágenes de Propiedades"
        ordering = ["-id"]

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

    class Meta:
        db_table = "rooms"
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"
        ordering = ["name"]
        unique_together = ("name", "property")

    def __str__(self):
        return f"{self.name} - {self.property.name}"

    def is_available(self, check_in, check_out):
        return not self.reservations.filter(
            check_in__lt=check_out,
            check_out__gt=check_in
        ).exists()


def room_image_upload_path(instance, filename):
    return f"properties/rooms/{filename}"


class RoomImage(models.Model):
    room = models.ForeignKey(Room, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=room_image_upload_path)

    class Meta:
        db_table = "room_images"
        verbose_name = "Imagen de Habitación"
        verbose_name_plural = "Imágenes de Habitaciones"
        ordering = ["-id"]

    def __str__(self):
        return f"Image de {self.room.name}"


class CommunicationMethod(models.Model):
    property = models.ForeignKey(Property, related_name="communication_methods", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    class Meta:
        db_table = "communication_methods"
        verbose_name = "Método de Comunicación"
        verbose_name_plural = "Métodos de Comunicación"
        ordering = ["name"]
        unique_together = ("property", "name")

    def __str__(self):
        return self.name
