from datetime import date

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


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
