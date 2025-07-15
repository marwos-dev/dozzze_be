from django.contrib import admin, messages
from django.contrib.gis.admin import GISModelAdmin
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from pms.utils.property_helper_factory import PMSHelperFactory
from properties.admin_utils.inlines import (
    CommunicationMethodInline,
    PMSDataInline,
    PropertyImageInline,
    RoomImageInline,
    RoomInline,
    RoomTypeImageInline,
    RoomTypeInline,
    TermsAndConditionsInline,
)
from properties.models import CommunicationMethod, Property, Room, RoomType, Service

from .sync_service import SyncService


@admin.register(Property)
class PropertyAdmin(GISModelAdmin):
    class Media:
        js = ("js/addPoligon.js",)
        css = {"all": ("css/map_solution.css",)}

    inlines = [
        PMSDataInline,
        PropertyImageInline,
        RoomTypeInline,
        CommunicationMethodInline,
        TermsAndConditionsInline,
    ]  # add "current_reservations"
    search_fields = ["name", "location", "rooms__pax"]
    list_display = (
        "name",
        "cover_preview",
        "location",
    )
    readonly_fields = ("owner",)
    # readonly_fields = ["recent_reservations"]
    pms_helper = PMSHelperFactory()
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
                    "description",
                    "active",
                    # "recent_reservations"
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

    def save_model(self, request, obj, form, change):
        if not change or not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_staff:
            return qs.filter(owner=request.user)
        return qs.none()  # los consumidores nunca deben ver nada

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff and obj and obj.owner == request.user:
            return True
        return False

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="100" />', obj.cover_image.url)
        return "-"

    cover_preview.short_description = "Cover"

    # def recent_reservations(self, obj: Property):
    #     reservations = obj.reservations.all().order_by("-created_at")[:10]
    #     html = "<ul>"
    #     for r in reservations:
    #         guest_name = r.guest_name or r.guest_corporate or "Sin nombre"
    #         html += f"<li>Reserva #{r.pk} a nombre de {guest_name} - {r.created_at.strftime('%Y-%m-%d')}</li>"
    #     html += "</ul>"
    #     return mark_safe(html)

    # recent_reservations.short_description = "Últimas reservas"

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
        if not prop or not isinstance(prop, Property):
            self.message_user(request, "Propiedad no encontrada.", level=messages.ERROR)
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        if not prop.pms:
            self.message_user(
                request,
                "La propiedad no tiene un PMS asociado.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse("admin:properties_property_change", args=[prop.pk])
            )

        if not prop.pms_data:
            self.message_user(
                request,
                "La propiedad no tiene datos de PMS asociados.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse("admin:properties_property_change", args=[prop.pk])
            )

        # Verificamos que los campos necesarios estén completos
        necesary_fields = [
            "pms_token",
            "pms_hotel_identifier",
            "pms_username",
            "pms_password",
            "email",
            "phone_number",
            "base_url",
        ]
        for field in necesary_fields:
            if not getattr(prop.pms_data, field):
                self.message_user(
                    request,
                    f"Falta el campo {field} para sincronizar con pms {prop.pms.name}.",
                    level=messages.ERROR,
                )
                return HttpResponseRedirect(
                    reverse("admin:properties_property_change", args=[prop.pk])
                )

        success = self.perform_pms_sync(request, prop)

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

    def perform_pms_sync(self, request, prop: Property):
        # Tu lógica real de sincronización acá
        helper = self.pms_helper.get_helper(prop)
        sync_detail = SyncService.sync_property_detail(prop, helper)
        if sync_detail:
            self.message_user(
                request,
                f"Datos de la propiedad {prop.name} actualizados correctamente.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                None,
                f"No se encontraron detalles para la propiedad {prop.name}.",
                level=messages.ERROR,
            )
            return False

        sync_rooms = SyncService.sync_rooms(prop, helper)
        if sync_rooms:
            self.message_user(
                request,
                f"Habitaciones de la propiedad {prop.name} actualizadas correctamente.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f"No se encontraron habitaciones para la propiedad {prop.name}.",
                level=messages.ERROR,
            )

        sync_reservations = SyncService.sync_reservations(prop, helper, request.user)
        if sync_reservations:
            self.message_user(
                request,
                f"Reservas de la propiedad {prop.name} actualizadas correctamente.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f"No se encontraron reservas para la propiedad {prop.name}.",
                level=messages.ERROR,
            )

        sync_availability = SyncService.sync_rates_and_availability(prop, helper)
        if sync_availability:
            self.message_user(
                request,
                f"Disponibilidad y tarifas de la propiedad {prop.name} actualizadas correctamente.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f"No se encontraron datos de disponibilidad y tarifas para la propiedad {prop.name}.",
                level=messages.ERROR,
            )
            return False

        if prop.pms_data.first_sync:
            prop.pms_data.first_sync = False
            prop.pms_data.save()

        return True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        prop = self.get_object(request, object_id)
        if prop:
            reservations = prop.reservations.all().order_by("-created_at")
            page_obj = Paginator(reservations, 10).get_page(request.GET.get("page", 1))

            extra_context.update(
                {
                    "sync_button": format_html(
                        '<a class="btn btn-info" href="{}">Sincronizar con PMS</a>',
                        reverse("admin:sync_property_with_pms", args=[object_id]),
                    ),
                    "recent_reservations": page_obj,
                }
            )

        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    inlines = [RoomImageInline]  # ReservationInline
    list_display = ("name", "property", "pax")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_staff:
            return qs.filter(property__owner=request.user)
        return qs.none()


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_staff:
            return qs.filter(property__owner=request.user)
        return qs.none()


@admin.register(CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_staff:
            return qs.filter(property__owner=request.user)
        return qs.none()


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [RoomInline, RoomTypeImageInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_staff:
            return qs.filter(rooms__property__owner=request.user)
        return qs.none()
