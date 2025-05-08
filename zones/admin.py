from django.contrib import admin
from django.utils.html import format_html
from django.contrib.gis.admin import GISModelAdmin

from .models import Zone, ZoneImage

class ZoneImageInline(admin.TabularInline):
    model = ZoneImage
    extra = 1

@admin.register(Zone)
class ZoneAdmin(GISModelAdmin):
    inlines = [ZoneImageInline]
    list_display = ("name",)

    # Centrar el mapa en España
    gis_widget_kwargs = {
        'attrs': {
            'default_lon': -3.7038,
            'default_lat': 40.4168,
            'default_zoom': 6,
        }
    }

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="100" />', obj.cover_image.url)
        return "-"
    cover_preview.short_description = "Cover"
