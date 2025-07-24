from django.contrib import admin, messages
from django.contrib.gis.admin import GISModelAdmin
from django.contrib.gis.geos import Point
from geopy.geocoders import Nominatim
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import (
    CommunicationFormSet,
    PmsDataForm,
    PropertyImagesForm,
    PropertyStepForm,
)

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

    def add_view(self, request, form_url="", extra_context=None):
        if request.user.is_staff and not request.user.is_superuser:
            return HttpResponseRedirect(
                reverse("admin:properties_property_add_step", args=[1])
            )
        return super().add_view(request, form_url, extra_context)

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
            path(
                "add/step/<int:step>/",
                self.admin_site.admin_view(self.add_stepper),
                name="properties_property_add_step",
            ),
            path(
                "dashboard/",
                self.admin_site.admin_view(self.dashboard_view),
                name="properties_dashboard",
            ),
        ]
        return custom_urls + urls

    def add_stepper(self, request, step):
        property_id = request.session.get("new_property_id")

        if step == 1:
            form = PropertyStepForm(request.POST or None, request.FILES or None)
            if request.method == "POST" and form.is_valid():
                prop = form.save(commit=False)
                prop.owner = request.user
                prop.save()

                try:
                    address = f"{prop.address}, {prop.zone.name if prop.zone else ''}"
                    geolocator = Nominatim(user_agent="dozzze_admin")
                    location = geolocator.geocode(address)
                    if location:
                        prop.location = Point(location.longitude, location.latitude)
                    else:
                        prop.location = Point(0, 0)
                    prop.save(update_fields=["location"])
                except Exception as exc:
                    prop.location = Point(0, 0)
                    prop.save(update_fields=["location"])
                    self.message_user(
                        request,
                        "No se pudo geolocalizar la propiedad automáticamente.",
                        level=messages.WARNING,
                    )

                request.session["new_property_id"] = prop.pk
                return HttpResponseRedirect(
                    reverse("admin:properties_property_add_step", args=[2])
                )
            return TemplateResponse(
                request,
                "admin/properties/property/add_step1.html",
                {"form": form},
            )

        if not property_id:
            return HttpResponseRedirect(
                reverse("admin:properties_property_add_step", args=[1])
            )

        prop = Property.objects.filter(pk=property_id, owner=request.user).first()
        if not prop:
            return HttpResponseRedirect(
                reverse("admin:properties_property_add_step", args=[1])
            )

        if step == 2:
            instance = getattr(prop, "pms_data", None)
            form = PmsDataForm(request.POST or None, instance=instance)
            if request.method == "POST" and form.is_valid():
                pms_data = form.save(commit=False)
                pms_data.property = prop
                pms_data.save()
                helper = PMSHelperFactory().get_helper(prop)
                SyncService.sync_property_detail(prop, helper)
                return HttpResponseRedirect(
                    reverse("admin:properties_property_add_step", args=[3])
                )
            return TemplateResponse(
                request,
                "admin/properties/property/add_step2.html",
                {"form": form},
            )

        if step == 3:
            form = PropertyImagesForm(request.POST or None, request.FILES or None)
            if request.method == "POST" and form.is_valid():
                for img in request.FILES.getlist("images"):
                    PropertyImage.objects.create(property=prop, image=img)
                return HttpResponseRedirect(
                    reverse("admin:properties_property_add_step", args=[4])
                )
            return TemplateResponse(
                request,
                "admin/properties/property/add_step3.html",
                {"form": form},
            )

        if step == 4:
            formset = CommunicationFormSet(request.POST or None)
            if request.method == "POST" and formset.is_valid():
                for form in formset:
                    if form.cleaned_data.get("name") and form.cleaned_data.get("value"):
                        CommunicationMethod.objects.create(
                            property=prop,
                            name=form.cleaned_data["name"],
                            value=form.cleaned_data["value"],
                        )
                del request.session["new_property_id"]
                self.message_user(request, "Propiedad creada correctamente")
                return HttpResponseRedirect(
                    reverse("admin:properties_property_change", args=[prop.pk])
                )
            return TemplateResponse(
                request,
                "admin/properties/property/add_step4.html",
                {"formset": formset},
            )

        return HttpResponseRedirect(
            reverse("admin:properties_property_add_step", args=[1])
        )

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
                    "dashboard_button": format_html(
                        '<a class="btn btn-primary" href="{}">Ir al Dashboard</a>',
                        reverse("admin:properties_dashboard"),
                    ),
                }
            )

        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def dashboard_view(self, request):
        from django.db.models import Sum

        from reservations.models import ReservationRoom

        data = (
            ReservationRoom.objects.filter(reservation__property__owner=request.user)
            .values(
                "reservation__property__name",
                "room_type__name",
            )
            .annotate(total=Sum("price"))
        )

        properties = sorted({d["reservation__property__name"] for d in data})
        room_types = sorted({d["room_type__name"] for d in data})

        datasets = []
        colors = [
            "#ff6384",
            "#36a2eb",
            "#cc65fe",
            "#ffce56",
            "#2ecc71",
            "#e67e22",
            "#1abc9c",
            "#e74c3c",
        ]
        for i, rt in enumerate(room_types):
            values = []
            for prop in properties:
                val = 0
                for entry in data:
                    if (
                        entry["reservation__property__name"] == prop
                        and entry["room_type__name"] == rt
                    ):
                        val = entry["total"] or 0
                        break
                values.append(val)
            datasets.append(
                {
                    "label": rt or "N/A",
                    "data": values,
                    "color": colors[i % len(colors)],
                }
            )

        context = {
            "title": "Dashboard",
            "labels": properties,
            "datasets": datasets,
        }
        return TemplateResponse(
            request,
            "admin/properties/property/dashboard.html",
            context,
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
