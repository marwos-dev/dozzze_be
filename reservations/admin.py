from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "check_in", "check_out", "created_at")
    list_filter = ("check_in", "check_out")
    search_fields = ("guest_name", "guest_email")
    exclude = ("user",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)
