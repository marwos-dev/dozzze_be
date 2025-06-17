from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html

from .models import Zone, ZoneImage


class ZoneImageInline(admin.TabularInline):
    model = ZoneImage
    extra = 1


@admin.register(Zone)
class ZoneAdmin(GISModelAdmin):
    inlines = [
        ZoneImageInline,
    ]
    list_display = ("name",)
    default_lon = -3.7038
    default_lat = 40.4168
    default_zoom = 6
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "area",
                    "active",
                    "cover_image",
                )
            },
        ),
    )
    readonly_fields = ("created_at",)

    class Media:
        css = {"all": ("css/map_solution.css",)}

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="100" />', obj.cover_image.url)
        return "-"

    cover_preview.short_description = "Cover"
