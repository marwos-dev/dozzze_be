from typing import Optional
from uuid import uuid4

from django.contrib.gis.db import models as geomodels
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage


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
    return f"properties/cover_image/{uuid4()}-{filename}"


class Property(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripcion")
    address = models.CharField(max_length=255, verbose_name="Dirección")
    location = geomodels.PointField(geography=True, verbose_name="Ubicación")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    cover_image = models.ImageField(
        upload_to=property_cover_image_upload_path,
        null=True,
        blank=True,
        verbose_name="Imagen",
        storage=S3Boto3Storage(),
    )
    zone = models.ForeignKey(
        "zones.Zone",
        related_name="properties",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Zona",
    )
    pms = models.ForeignKey(
        "pms.PMS",
        related_name="properties",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        verbose_name="PMS",
    )
    use_pms_information = models.BooleanField(
        default=False,
        verbose_name="Usar información del PMS",
        help_text="Si está marcado, se utilizará la información del PMS para esta propiedad.",
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
    return f"properties/gallery/{uuid4()}-{filename}"


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property, related_name="gallery", on_delete=models.CASCADE, verbose_name="Zona"
    )
    image = models.ImageField(
        upload_to=property_image_upload_path,
        verbose_name="Imagen",
        storage=S3Boto3Storage(),
    )
    caption = models.CharField(max_length=255, blank=True, verbose_name="Descripción")

    class Meta:
        db_table = "property_images"
        verbose_name = "Imagen de Propiedad"
        verbose_name_plural = "Imágenes de Propiedades"
        ordering = ["-id"]

    def __str__(self):
        return f"Image of {self.property.name}"


class RoomType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    external_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="ID Externo"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        db_table = "room_types"
        verbose_name = "Tipo de Habitación"
        verbose_name_plural = "Tipos de Habitaciones"
        ordering = ["name"]

    def __str__(self):
        return self.name


    def photos_of_room_type(self):
        return self.rooms.filter(images__isnull=False).values_list('images__image', flat=True)


class Room(models.Model):
    property = models.ForeignKey(
        Property, related_name="rooms", on_delete=models.CASCADE
    )
    type = models.ForeignKey(
        RoomType,
        related_name="rooms",
        on_delete=models.CASCADE,
        verbose_name="Tipo de Habitación",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    pax = models.PositiveIntegerField()
    services = models.ManyToManyField(Service, blank=True)
    external_id = models.CharField(max_length=255, null=True, blank=True)
    external_room_type_id = models.CharField(max_length=255, null=True, blank=True)
    external_room_type_name = models.CharField(max_length=255, null=True, blank=True)

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
            check_in__lt=check_out, check_out__gt=check_in
        ).exists()

    @classmethod
    def get_type_room_from_name(cls, name) -> Optional[str]:
        if (
                "habitacion" in name.lower()
                or "room" in name.lower()
                or "cuarto" in name.lower()
        ):
            return cls.ROOM

        if (
                "apartamento" in name.lower()
                or "apartament" in name.lower()
                or "departamento" in name.lower()
        ):
            return cls.APARTMENT

        if "estudio" in name.lower() or "studio" in name.lower():
            return cls.STUDIO

        for room_type in cls.ROOM_TYPES:
            if room_type[1].lower() in name.lower():
                return room_type[0]

        print(f"Tipo de habitación desconocido para el nombre: {name}")
        print("Por defecto, se asignará 'Room'.")
        return cls.ROOM


def room_image_upload_path(instance, filename):
    return f"properties/gallery/{uuid4()}-{filename}"


class RoomImage(models.Model):
    room = models.ForeignKey(Room, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to=room_image_upload_path, storage=S3Boto3Storage()
    )

    class Meta:
        db_table = "room_images"
        verbose_name = "Imagen de Habitación"
        verbose_name_plural = "Imágenes de Habitaciones"
        ordering = ["-id"]

    def __str__(self):
        return f"Image de {self.room.name}"


class CommunicationMethod(models.Model):
    property = models.ForeignKey(
        Property, related_name="communication_methods", on_delete=models.CASCADE
    )
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


class TermsAndConditions(models.Model):
    property = models.OneToOneField(
        Property, related_name="terms_and_conditions", on_delete=models.CASCADE
    )
    condition_of_confirmation = models.TextField(
        null=True, blank=True, verbose_name="Condición de Confirmación"
    )
    check_in_time = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Hora de Check-in"
    )
    check_out_time = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Hora de Check-out"
    )
    cancellation_policy = models.TextField(
        null=True, blank=True, verbose_name="Política de Cancelación"
    )
    additional_information = models.TextField(
        null=True, blank=True, verbose_name="Información Adicional"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        db_table = "terms_and_conditions"
        verbose_name = "Términos y Condiciones"
        verbose_name_plural = "Términos y Condiciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Términos y Condiciones de {self.property.name}"


class PmsDataProperty(models.Model):
    property = models.OneToOneField(
        Property, related_name="pms_data", on_delete=models.CASCADE
    )
    base_url = models.CharField(
        max_length=255, verbose_name="Base URL", default=None, blank=True, null=True
    )
    email = models.EmailField(verbose_name="Email", default=None, blank=True, null=True)
    phone_number = models.CharField(
        max_length=255, verbose_name="Teléfono", default=None, blank=True, null=True
    )
    pms_token = models.CharField(null=True, blank=True, default=None)
    pms_hotel_identifier = models.CharField(null=True, blank=True, default=None)
    pms_username = models.CharField(null=True, blank=True, default=None)
    pms_password = models.CharField(null=True, blank=True, default=None)

    pms_property_id = models.PositiveIntegerField(null=True, blank=True, default=None)
    pms_property_name = models.CharField(
        max_length=255, null=True, blank=True, default=None
    )
    pms_property_address = models.CharField(
        max_length=255, null=True, blank=True, default=None
    )
    pms_property_city = models.CharField(
        max_length=255, null=True, blank=True, default=None
    )
    pms_property_province = models.CharField(
        max_length=255, null=True, blank=True, default=None
    )
    pms_property_postal_code = models.CharField(
        max_length=20, null=True, blank=True, default=None
    )
    pms_property_country = models.CharField(
        max_length=255, null=True, blank=True, default=None
    )
    pms_property_latitude = models.FloatField(
        null=True, blank=True, default=None, verbose_name="Latitud"
    )
    pms_property_longitude = models.FloatField(
        null=True, blank=True, default=None, verbose_name="Longitud"
    )
    pms_property_phone = models.CharField(
        max_length=255, null=True, blank=True, default=None, verbose_name="Teléfono PMS"
    )
    pms_property_category = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="Categoría PMS",
    )
    first_sync = models.BooleanField(
        default=True,
        verbose_name="Primera sincronización",
    )

    class Meta:
        db_table = "pms_data_property"
        verbose_name = "Datos PMS"
        verbose_name_plural = "Datos PMS"

    def __str__(self):
        return f"PMS Data for {self.property.name}"


class Availability(models.Model):
    property = models.ForeignKey(
        Property, related_name="availability", on_delete=models.CASCADE
    )
    room_type = models.ForeignKey(
        RoomType,
        related_name="availability",
        on_delete=models.CASCADE,
        verbose_name="Tipo de Habitación",
    )
    date = models.DateField()
    availability = models.IntegerField()
    rates = models.JSONField(null=True, blank=True, default=None)

    class Meta:
        db_table = "availability"
        verbose_name = "Disponibilidad"
        verbose_name_plural = "Disponibilidades"
        unique_together = ("property", "room_type", "date")
        ordering = ["-date"]


