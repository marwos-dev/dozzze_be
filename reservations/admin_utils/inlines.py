from django.contrib import admin


class ReservationInline(admin.TabularInline):
    model = "reservations.Reservation"
    extra = 1
    show_change_link = True
