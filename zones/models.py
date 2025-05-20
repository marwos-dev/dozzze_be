from uuid import uuid4

from django.contrib.gis.db import models as geomodels
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage


def zone_cover_image_upload_path(instance, filename):
    return f"zones/cover_image/{uuid4()}-{filename}"


class Zone(models.Model):
    name = models.CharField(verbose_name="Nombre", max_length=255)
    description = models.TextField(verbose_name="Descripción")
    area = geomodels.PolygonField(geography=True, null=True, blank=True)
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    cover_image = models.ImageField(
        upload_to=zone_cover_image_upload_path,
        null=True,
        blank=True,
        verbose_name="Imagen",
        storage=S3Boto3Storage(),
    )

    class Meta:
        db_table = "zones"
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"

    def __str__(self):
        return self.name


def zone_image_upload_path(instance, filename):
    return f"zone/gallery/{uuid4()}-{filename}"


class ZoneImage(models.Model):
    zone = models.ForeignKey(
        Zone, related_name="zone_images", on_delete=models.CASCADE, verbose_name="Zona"
    )
    image = models.ImageField(
        upload_to=zone_image_upload_path,
        verbose_name="Imagen",
        storage=S3Boto3Storage(),
    )
    caption = models.CharField(max_length=255, blank=True, verbose_name="Descripción")

    class Meta:
        db_table = "zone_images"
        verbose_name = "Imagen de Zona"
        verbose_name_plural = "Imágenes de Zonas"

    def __str__(self):
        return f"Imagen de Zona {self.zone.name}"
