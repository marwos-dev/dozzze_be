from django.db import models

# Create your models here.


class PMS(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)
    has_integration = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "pms"
        verbose_name = "PMS"
        verbose_name_plural = "PMS"
        ordering = ["name"]
