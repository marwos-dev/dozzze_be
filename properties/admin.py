from datetime import date

from django import forms
from django.contrib import admin, messages
from django.contrib.gis.admin import GISModelAdmin
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# from pms.utils.property_helper_factory import get_property_helper
from reservations.models import Reservation

from .models import (
    CommunicationMethod,
    Property,
    PropertyImage,
    Room,
    RoomImage,
    Service,
    TermsAndConditions,
)


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


class RoomInline(admin.StackedInline):
    model = Room
    extra = 1
    show_change_link = True


class TermsAndConditionsInline(admin.StackedInline):
    model = TermsAndConditions
    extra = 1


class CommunicationMethodInline(admin.TabularInline):
    model = CommunicationMethod
    extra = 1


class AvailabilityFilter(admin.SimpleListFilter):
    title = _("Disponibilidad")
    parameter_name = "availability"

    def lookups(self, request, model_admin):
        return [
            ("available", _("Disponible hoy")),
            ("unavailable", _("Ocupada hoy")),
        ]

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == "available":
            return queryset.exclude(
                reservations__check_in__lte=today, reservations__check_out__gt=today
            )
        if self.value() == "unavailable":
            return queryset.filter(
                reservations__check_in__lte=today, reservations__check_out__gt=today
            )
        return queryset


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class ReservationInlineForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["room", "guest_name", "guest_email", "check_in", "check_out", "user"]
        readonly_fields = ["guest_name", "guest_email", "check_in", "check_out", "user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.room:
            property_instance = self.instance.room.property
            self.fields["room"].queryset = Room.objects.filter(
                property=property_instance
            )


class ReservationInlineFormSet(BaseInlineFormSet):
    readonly_fields = ["guest_name", "guest_email", "check_in", "check_out", "user"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self.instance, "property"):  # solo si self.instance es un Room
            property_instance = self.instance.property
            for form in self.forms:
                form.fields["room"].queryset = Room.objects.filter(
                    property=property_instance
                )
        else:
            for form in self.forms:
                form.fields["room"].queryset = Room.objects.all()


class ReservationInline(admin.TabularInline):
    model = Reservation
    form = ReservationInlineForm
    formset = ReservationInlineFormSet
    extra = 1


@admin.register(Property)
class PropertyAdmin(GISModelAdmin):
    class Media:
        js = ("js/addPoligon.js",)
        css = {"all": ("css/map_solution.css",)}

    inlines = [
        PropertyImageInline,
        RoomInline,
        CommunicationMethodInline,
        TermsAndConditionsInline,
    ]  # add "current_reservations"
    search_fields = ["name", "location", "rooms__pax"]
    list_display = (
        "name",
        "cover_preview",
        "location",
    )
    # readonly_fields = ["reservations_table"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "zone",
                    "location",
                    "cover_image",
                    "pms",
                    "pms_token",
                    "pms_hotel_identifier",
                    "pms_username",
                    "pms_password",
                    "base_url",
                    "description",
                    "active",
                )  # add 'reservations_table'
            },
        ),
    )

    gis_widget_kwargs = {
        "attrs": {
            "default_lon": -3.7038,
            "default_lat": 40.4168,
            "default_zoom": 6,
        }
    }

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="100" />', obj.cover_image.url)
        return "-"

    cover_preview.short_description = "Cover"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:property_id>/sync-pms/",
                self.admin_site.admin_view(self.sync_with_pms),
                name="sync_property_with_pms",
            ),
        ]
        return custom_urls + urls

    def sync_with_pms(self, request, property_id):
        prop = self.get_object(request, property_id)
        if not prop:
            self.message_user(request, "Propiedad no encontrada.", level=messages.ERROR)
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        necesary_fields = [
            "pms",
            "pms_token",
            "pms_hotel_identifier",
            "pms_username",
            "pms_password",
        ]
        for field in necesary_fields:
            if not getattr(prop, field):
                self.message_user(
                    request,
                    f"Falta el campo {field} para sincronizar con PMS {prop.pms.name}.",
                    level=messages.ERROR,
                )
                return HttpResponseRedirect(
                    reverse("admin:properties_property_change", args=[prop.pk])
                )

        success = self.perform_pms_sync(prop)

        if success:
            self.message_user(
                request,
                f"Sincronización con PMS  {prop.pms.name}. exitosa",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f"Fallo al sincronizar con el PMS {prop.pms.name}.",
                level=messages.ERROR,
            )

        return HttpResponseRedirect(
            reverse("admin:properties_property_change", args=[prop.pk])
        )

    def perform_pms_sync(self, prop):
        # Tu lógica real de sincronización acá
        # helper = get_property_helper(prop.pms)

        # Definí el rango de fechas que querés usar (ejemplo: 1 mes)
        # start_date_id = 202301  # ejemplo: YYYYMM
        # end_date_id = 202312

        # Hacemos las extracciones necesarias
        # availability = helper.download_availability(prop, start_date_id, end_date_id)
        # revenue = helper.download_revenue(prop, start_date_id, end_date_id)
        # blocked = helper.download_blocked(prop, start_date_id, end_date_id)

        return bool(prop.pms and prop.pms_token)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        sync_url = reverse("admin:sync_property_with_pms", args=[object_id])
        extra_context["sync_button"] = format_html(
            '<a class="btn btn-info" href="{}">Sincronizar con PMS</a>', sync_url
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    # def current_reservations(self, obj):
    #     return Reservation.objects.filter(room__property=obj, check_out__gte=timezone.now().date()).count()
    #
    # current_reservations.short_description = "Reservas activas"

    # def reservations_table(self, obj):
    #     if not isinstance(obj, Property):
    #         return _("Error: se esperaba una propiedad.")
    #
    #     reservations = Reservation.objects.filter(room__property=obj).select_related("room")
    #     if not reservations.exists():
    #         return _("No hay reservas asociadas.")
    #
    #     rows = "".join(
    #         f"<tr><td>{r.id}</td><td>{r.room.name}</td><td>{r.check_in}</td><td>{r.check_out}</td></tr>"
    #         for r in reservations
    #     )
    #     table = f"""
    #     <table style="border-collapse: collapse; width: 100%;">
    #         <thead>
    #             <tr>
    #                 <th style="border: 1px solid #ddd; padding: 8px;">ID</th>
    #                 <th style="border: 1px solid #ddd; padding: 8px;">Habitación</th>
    #                 <th style="border: 1px solid #ddd; padding: 8px;">Check-in</th>
    #                 <th style="border: 1px solid #ddd; padding: 8px;">Check-out</th>
    #             </tr>
    #         </thead>
    #         <tbody>{rows}</tbody>
    #     </table>
    #     """
    #     return mark_safe(table)
    #
    # reservations_table.short_description = "Reservas relacionadas"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    inlines = [RoomImageInline]  # ReservationInline
    list_display = ("name", "property", "pax")
    filter_horizontal = ("services",)
    # list_filter = (AvailabilityFilter,)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = ("name",)
