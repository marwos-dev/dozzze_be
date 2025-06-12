from django.db import models


class PMS(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)
    pms_external_id = models.CharField(
        max_length=255, unique=True, blank=True, null=True
    )
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


class PMSDataResponse(models.Model):
    pms = models.ForeignKey(
        PMS, on_delete=models.CASCADE, related_name="pms_data_responses"
    )
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="pms_data_responses",
    )
    function_name = models.CharField(max_length=255)
    response_data = models.JSONField(verbose_name="Response Data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(null=True, blank=True, default=None)
    end_date = models.DateField(null=True, blank=True, default=None)

    class Meta:
        db_table = "pms_data_response"
        verbose_name = "PMS Data Response"
        verbose_name_plural = "PMS Data Responses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"PMS Data Response for {self.pms.name} at {self.created_at}"
