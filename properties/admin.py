from datetime import date

from django import forms
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.forms.models import BaseInlineFormSet
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from reservations.models import Reservation
from .models import CommunicationMethod, Property, PropertyImage, Room, RoomImage, Service


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


class RoomInline(admin.StackedInline):
    model = Room
    extra = 1
    show_change_link = True


class CommunicationMethodInline(admin.TabularInline):
    model = CommunicationMethod
    extra = 1


class AvailabilityFilter(admin.SimpleListFilter):
    title = _('Disponibilidad')
    parameter_name = 'availability'

    def lookups(self, request, model_admin):
        return [
            ('available', _('Disponible hoy')),
            ('unavailable', _('Ocupada hoy')),
        ]

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'available':
            return queryset.exclude(
                reservations__check_in__lte=today,
                reservations__check_out__gt=today
            )
        if self.value() == 'unavailable':
            return queryset.filter(
                reservations__check_in__lte=today,
                reservations__check_out__gt=today
            )
        return queryset


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class ReservationInlineForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.room:
            property_instance = self.instance.room.property
            self.fields['room'].queryset = Room.objects.filter(property=property_instance)


class ReservationInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for form in self.forms:
            form.fields['room'].queryset = Room.objects.filter(property=self.instance)


class ReservationInline(admin.TabularInline):
    model = Reservation
    form = ReservationInlineForm
    formset = ReservationInlineFormSet
    extra = 1


@admin.register(Property)
class PropertyAdmin(GISModelAdmin):
    inlines = [PropertyImageInline, RoomInline, CommunicationMethodInline]
    list_display = ("name", "cover_preview", "location", "current_reservations")
    search_fields = ['name', 'location', 'rooms__pax']
    readonly_fields = ["reservations_table"]

    fieldsets = (
        (None, {
            'fields': ('name', 'location', 'cover_image', 'reservations_table')
        }),
    )

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

    def current_reservations(self, obj):
        return Reservation.objects.filter(room__property=obj, check_out__gte=timezone.now().date()).count()
    current_reservations.short_description = "Reservas activas"

    def reservations_table(self, obj):
        reservations = Reservation.objects.filter(room__property=obj).select_related("room")
        if not reservations.exists():
            return _("No hay reservas asociadas.")

        rows = "".join(
            f"<tr><td>{r.id}</td><td>{r.room.name}</td><td>{r.check_in}</td><td>{r.check_out}</td></tr>"
            for r in reservations
        )
        table = f"""
        <table style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px;">ID</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Habitación</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Check-in</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Check-out</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
        return mark_safe(table)

    reservations_table.short_description = "Reservas relacionadas"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    inlines = [RoomImageInline, ReservationInline]
    list_display = ("name", "property", "pax")
    filter_horizontal = ("services",)
    list_filter = (AvailabilityFilter,)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = ("name",)
