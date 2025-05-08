from django.contrib.gis.db import models as geomodels
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage



class Zone(models.Model):
    name = models.CharField(verbose_name="Nombre", max_length=255)
    description = models.TextField(verbose_name="Descripción")
    area = geomodels.PolygonField(geography=True, null=True, blank=True)
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    cover_image = models.ImageField(upload_to='zones/covers/', null=True, blank=True, verbose_name="Imagen", storage=S3Boto3Storage())

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ["name"]
        unique_together = ("name", )


class ZoneImage(models.Model):
    zone = models.ForeignKey(Zone, related_name='gallery', on_delete=models.CASCADE, verbose_name="Zona")
    image = models.ImageField(upload_to='zones/gallery/', verbose_name="Imagen", storage=S3Boto3Storage())
    caption = models.CharField(max_length=255, blank=True, verbose_name="Descripción")

    def __str__(self):
        return f"Imagen de Zona {self.zone.name}"

    class Meta:
        verbose_name = "Imagen de Zona"
        verbose_name_plural = "Imágenes de Zonas"
        ordering = ["-id"]
