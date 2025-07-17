from django.contrib import admin, messages

from utils.email_service import EmailService
from utils.error_codes import ReservationError

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "check_in", "check_out", "status", "created_at")
    list_filter = ("check_in", "check_out")
    search_fields = ("guest_name", "guest_email", "reservations__room_type__name")
    exclude = ("user",)
    readonly_fields = ("room_types_reserved",)
    actions = ["cancel_reservations", "mark_refunded"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def room_types_reserved(self, obj):
        room_types = obj.reservations.select_related("room_type").all()
        return ", ".join(set(rr.room_type.name for rr in room_types if rr.room_type))

    def cancel_reservations(self, request, queryset):
        for reservation in queryset:
            try:
                reservation.cancel()
            except ReservationError as e:
                self.message_user(request, str(e), level=messages.ERROR)
                continue

            if reservation.guest_email:
                EmailService.send_email(
                    subject="Cancelación en proceso",
                    to_email=reservation.guest_email,
                    template_name="emails/reservation_cancellation_processing.html",
                    context={"reservation": reservation},
                )

            owner_email = getattr(reservation.property.owner, "email", None)
            if owner_email:
                EmailService.send_email(
                    subject="Reserva pendiente de devolución",
                    to_email=owner_email,
                    template_name="emails/reservation_cancellation_owner_notice.html",
                    context={"reservation": reservation},
                )

        self.message_user(request, "Reservas canceladas")

    cancel_reservations.short_description = "Cancelar reservas seleccionadas"

    def mark_refunded(self, request, queryset):
        updated = 0
        for reservation in queryset:
            try:
                reservation.mark_refunded()
                updated += 1
            except ReservationError as e:
                self.message_user(request, str(e), level=messages.ERROR)

        if updated:
            self.message_user(request, f"{updated} reservas marcadas como devueltas")

    mark_refunded.short_description = "Marcar como devuelto"

    room_types_reserved.short_description = "Tipos de habitación reservados"
