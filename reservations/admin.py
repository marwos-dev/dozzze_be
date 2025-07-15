from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "check_in", "check_out", "created_at")
    list_filter = ("check_in", "check_out")
    search_fields = ("guest_name", "guest_email", "reservations__room_type__name")
    exclude = ("user",)
    readonly_fields = ("room_types_reserved",)

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

    room_types_reserved.short_description = "Tipos de habitación reservados"
