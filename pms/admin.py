from django.contrib import admin

from .models import PMS


@admin.register(PMS)
class PMSAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "has_integration", "created_at", "updated_at")
    list_filter = ("active", "has_integration")
    search_fields = ("name",)
    ordering = ("-created_at",)
    list_per_page = 20
