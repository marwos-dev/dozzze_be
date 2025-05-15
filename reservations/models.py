from django.db import models

from properties.models import Room  # asegurate que la app 'properties' exista


class Reservation(models.Model):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (CANCELLED, "Cancelled"),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reservations", verbose_name="Propiedad")
    guest_name = models.CharField(max_length=255, verbose_name="Nombre del huésped")
    guest_email = models.EmailField(verbose_name="Email del huésped")
    guest_phone = models.CharField(max_length=255, verbose_name="Teléfono del huésped")
    check_in = models.DateField(verbose_name="Checkin")
    check_out = models.DateField(verbose_name="Checkout")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Estado"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")
    user = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name="reservations", verbose_name="Usuario"
    )
    pax_count = models.IntegerField(default=1, verbose_name="Cantidad de personas")

    class Meta:
        db_table = "reservations"
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        unique_together = ("room", "check_in", "check_out")

    def __str__(self):
        return f"Reserva en {self.room.property.name}, habitacion {self.room.name} del {self.check_in} al {self.check_out}"
