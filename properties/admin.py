from datetime import datetime

from django.contrib import admin, messages
from django.contrib.gis.admin import GISModelAdmin
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
    TermsAndConditionsInline,
)
from properties.models import CommunicationMethod, Property, Room, Service
from reservations.models import Reservation, ReservationRoom
from utils.text_utils import extract_pax


@admin.register(Property)
class PropertyAdmin(GISModelAdmin):
    class Media:
        js = ("js/addPoligon.js",)
        css = {"all": ("css/map_solution.css",)}

    inlines = [
        PMSDataInline,
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
        sync_detail = self._sync_property_detail(prop, helper)
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

        sync_rooms = self._sync_rooms(prop, helper)
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

        sync_reservations = self._sync_reservations(prop, helper, request.user)
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

        return True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        sync_url = reverse("admin:sync_property_with_pms", args=[object_id])
        extra_context["sync_button"] = format_html(
            '<a class="btn btn-info" href="{}">Sincronizar con PMS</a>', sync_url
        )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def _sync_property_detail(self, prop: Property, helper):
        property_detail = helper.download_property_details(prop)
        if not property_detail:
            return False

        pms_data = prop.pms_data

        pms_data.pms_property_id = property_detail.get(
            "pms_property_id", pms_data.pms_property_id
        )
        pms_data.pms_property_name = property_detail.get(
            "pms_property_name", pms_data.pms_property_name
        )
        pms_data.pms_property_address = property_detail.get(
            "pms_property_address", pms_data.pms_property_address
        )
        pms_data.pms_property_city = property_detail.get(
            "pms_property_city", pms_data.pms_property_city
        )
        pms_data.pms_property_province = property_detail.get(
            "pms_property_province", pms_data.pms_property_province
        )
        pms_data.pms_property_postal_code = property_detail.get(
            "pms_property_postal_code", pms_data.pms_property_postal_code
        )
        pms_data.pms_property_country = property_detail.get(
            "pms_property_country", pms_data.pms_property_country
        )
        pms_data.pms_property_latitude = property_detail.get(
            "pms_property_latitude", pms_data.pms_property_latitude
        )
        pms_data.pms_property_longitude = property_detail.get(
            "pms_property_longitude", pms_data.pms_property_longitude
        )
        pms_data.pms_property_phone = property_detail.get(
            "pms_property_phone", pms_data.pms_property_phone
        )
        pms_data.pms_property_category = property_detail.get(
            "pms_property_category", pms_data.pms_property_category
        )
        pms_data.save()

        return True

    def _sync_rooms(self, prop: Property, helper):
        rooms_grouped_by_type = helper.download_room_list(prop)
        if not rooms_grouped_by_type:
            return False

        # Aquí podrías guardar las habitaciones en la base de datos si es necesario
        for room_type_id in rooms_grouped_by_type:
            for room in rooms_grouped_by_type[room_type_id]:
                # Asegúrate de que room tenga los campos necesarios
                if "taquilla" in room["external_room_type_name"].lower():
                    continue
                room_type = Room.get_type_room_from_name(
                    room["external_room_type_name"]
                )
                pax = extract_pax(room["external_room_type_name"])
                Room.objects.update_or_create(
                    property=prop,
                    name=room["name"],
                    type=room_type,
                    external_id=room.get("external_id", ""),
                    external_room_type_id=room.get("external_room_type_id", ""),
                    external_room_type_name=room.get("external_room_type_name", ""),
                    pax=pax,
                    defaults={
                        "description": room.get("description", ""),
                    },
                )
        return True

    def _sync_reservations(self, prop: Property, helper, user):
        reservations_data = helper.download_reservations(prop)
        if not reservations_data:
            return False

        reservations_to_create = []
        reservations_rooms_to_create = []
        for reservation_data in reservations_data:

            already_exist = Reservation.objects.filter(
                user=user,
                check_in=datetime.strptime(
                    reservation_data["check_in"], "%Y-%m-%d"
                ).date(),
                check_out=datetime.strptime(
                    reservation_data["check_out"], "%Y-%m-%d"
                ).date(),
                guest_name=reservation_data["guest_name"],
            ).exists()
            if already_exist:
                print(f"Reservation already exists for: {reservation_data}")
                continue

            reservation = Reservation(
                user=user,
                check_in=datetime.strptime(
                    reservation_data["check_in"], "%Y-%m-%d"
                ).date(),
                check_out=datetime.strptime(
                    reservation_data["check_out"], "%Y-%m-%d"
                ).date(),
                pax_count=reservation_data["rooms"]["occupancy"],
                total_price=reservation_data["total_price"],
                paid_online=reservation_data.get("paid_online", None),
                pay_on_arrival=reservation_data.get("pay_on_arrival", None),
                channel=reservation_data.get("channel", None),
                guest_name=reservation_data.get("guest_name", None),
                guest_corporate=reservation_data.get("guest_corporate", None),
                guest_email=reservation_data.get("guest_email", None),
                guest_phone=reservation_data.get("guest_phone", None),
                guest_address=reservation_data.get("guest_address", None),
                guest_city=reservation_data.get("guest_city", None),
                guest_region=reservation_data.get("guest_region", None),
                guest_country=reservation_data.get("guest_country", None),
                guest_country_iso=reservation_data.get("guest_country_iso", None),
                guest_cp=reservation_data.get("guest_cp", None),
                guest_remarks=reservation_data.get("guest_remarks", None),
                cancellation_date=reservation_data.get("cancellation_date", None),
                modification_date=reservation_data.get("modification_date", None),
                status=reservation_data.get("status", Reservation.PENDING),
            )
            reservations_to_create.append(reservation)

            rooms = None
            if rooms:
                reservation_room = ReservationRoom(
                    reservation=reservation,
                    room=rooms,
                    price=reservation_data.get("total_price", 0),
                    guests=reservation_data["room"]["occupancy"],
                )
                reservations_rooms_to_create.append(reservation_room)

        if reservations_to_create:
            Reservation.objects.bulk_create(reservations_to_create)

        if reservations_rooms_to_create:
            ReservationRoom.objects.bulk_create(reservations_rooms_to_create)

        return True


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    inlines = [RoomImageInline]  # ReservationInline
    list_display = ("name", "property", "pax")
    filter_horizontal = ("services",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(CommunicationMethod)
class CommunicationMethodAdmin(admin.ModelAdmin):
    list_display = ("name",)
