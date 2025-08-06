from django.core.exceptions import ValidationError
from django.db import models

from properties.models import Room, RoomType
from utils.error_codes import ReservationError, ReservationErrorCode


class ReservationRoom(models.Model):
    reservation = models.ForeignKey(
        "Reservation", on_delete=models.CASCADE, related_name="reservations"
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, null=True, blank=True
    )
    price = models.FloatField(null=True, blank=True)
    guests = models.IntegerField(default=1, verbose_name="Cantidad de huéspedes")

    class Meta:
        db_table = "reservation_rooms"
        unique_together = ("reservation", "room_type")
        verbose_name = "Habitación reservada"
        verbose_name_plural = "Habitaciones reservadas"

    def clean(self):
        overlapping = ReservationRoom.objects.filter(
            room=self.room,
            reservation__check_in__lt=self.reservation.check_out,
            reservation__check_out__gt=self.reservation.check_in,
        ).exclude(reservation=self.reservation)

        if overlapping.exists():
            raise ValidationError(
                "La habitación ya está reservada en ese rango de fechas."
            )


class Reservation(models.Model):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    PENDING_REFUND = "pending_refund"
    REFUNDED = "refunded"
    OK = "ok"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (PENDING_REFUND, "Pending refund"),
        (CANCELLED, "Cancelled"),
        (REFUNDED, "Refunded"),
        (OK, "Ok"),
    ]
    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Propiedad",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Estado"
    )
    rooms = models.ManyToManyField(
        Room,
        through="ReservationRoom",
        related_name="reservations",
    )
    # room_type = models.ForeignKey(
    #     "properties.RoomType",
    #     on_delete=models.CASCADE,
    #     related_name="reservations",
    # )
    guest_corporate = models.CharField(
        max_length=255,
        verbose_name="Nombre de la empresa del huésped",
        blank=True,
        null=True,
    )
    guest_name = models.CharField(
        max_length=255, verbose_name="Nombre del huésped", null=True, blank=True
    )
    guest_email = models.EmailField(
        verbose_name="Email del huésped", null=True, blank=True
    )
    guest_phone = models.CharField(
        max_length=255, verbose_name="Teléfono del huésped", null=True, blank=True
    )
    guest_address = models.CharField(
        max_length=255, verbose_name="Dirección del huésped", null=True, blank=True
    )
    guest_city = models.CharField(
        max_length=255, verbose_name="Ciudad del huésped", null=True, blank=True
    )
    guest_region = models.CharField(
        max_length=255, verbose_name="Región del huésped", null=True, blank=True
    )
    guest_country = models.CharField(
        max_length=255, verbose_name="País del huésped", null=True, blank=True
    )
    guest_country_iso = models.CharField(
        max_length=4,
        verbose_name="País del huésped (ISO)",
        default="US",
        null=True,
        blank=True,
    )
    guest_cp = models.CharField(
        max_length=40, verbose_name="Código postal del huésped", null=True, blank=True
    )
    guest_remarks = models.TextField(
        verbose_name="Observaciones del huésped", null=True, blank=True
    )

    channel = models.CharField(
        max_length=255, verbose_name="Nombre del channel", null=True, blank=True
    )
    channel_id = models.PositiveIntegerField(
        verbose_name="ID del channel", null=True, blank=True
    )

    check_in = models.DateField(verbose_name="Checkin", null=True, blank=True)
    check_out = models.DateField(verbose_name="Checkout", null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creacion"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de actualizacion"
    )
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Usuario",
        null=True,
        blank=True,
    )
    pax_count = models.IntegerField(default=1, verbose_name="Cantidad de personas")

    cancellation_date = models.DateTimeField(
        verbose_name="Cancellation date", null=True, blank=True
    )
    modification_date = models.DateTimeField(
        verbose_name="Modification date", null=True, blank=True
    )
    currency = models.CharField(verbose_name="Moneda", max_length=3, default="EUR")
    total_price = models.FloatField(verbose_name="Total price", null=True, blank=True)
    original_price = models.FloatField(
        verbose_name="Original price", null=True, blank=True
    )
    discount_amount = models.FloatField(
        verbose_name="Discount amount", default=0
    )
    paid_online = models.FloatField(verbose_name="Paid online", null=True, blank=True)
    pay_on_arrival = models.FloatField(
        verbose_name="Pay on arrival", null=True, blank=True
    )
    discount_coupon = models.ForeignKey(
        "vouchers.DiscountCoupon",
        on_delete=models.SET_NULL,
        related_name="reservations",
        null=True,
        blank=True,
    )

    # Campos para Redsys
    payment_order = models.CharField(max_length=12, null=True, blank=True)
    payment_amount = models.IntegerField(null=True, blank=True)  # En céntimos
    payment_signature = models.CharField(max_length=256, null=True, blank=True)
    payment_response = models.JSONField(null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")],
        default="pending",
    )
    payment_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reservations"
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

    def __str__(self):
        rooms = ", ".join([room.name for room in self.rooms.all()])
        return f"Reserva en {rooms} del {self.check_in} al {self.check_out}"

    def get_room_types(self):
        room_types = self.reservations.select_related("room_type").all()
        return ", ".join(set(rr.room_type.name for rr in room_types if rr.room_type))

    def apply_coupon(self, coupon):
        if coupon and coupon.active:
            if self.original_price is None:
                self.original_price = self.total_price
            discount = float(self.total_price) * float(coupon.discount_percent) / 100
            self.total_price = float(self.total_price) - discount
            self.discount_amount = float(self.discount_amount) + discount
            self.discount_coupon = coupon
            self.save(
                update_fields=[
                    "total_price",
                    "discount_amount",
                    "discount_coupon",
                    "original_price",
                ]
            )

    def apply_voucher(self, voucher, amount):
        if self.original_price is None:
            self.original_price = self.total_price
        voucher.redeem(amount, reservation=self)
        self.total_price = float(self.total_price) - float(amount)
        self.discount_amount = float(self.discount_amount) + float(amount)
        self.save(update_fields=["total_price", "discount_amount", "original_price"])

    def cancel(self):
        """Mark the reservation as pending refund if cancellation is allowed."""
        from django.utils import timezone

        if self.status in [Reservation.CANCELLED, Reservation.PENDING_REFUND]:
            raise ReservationError(
                "Reservation already cancelled",
                ReservationErrorCode.CANCEL_NOT_ALLOWED,
            )

        # Disallow cancellation if the reservation has been used
        if self.status == Reservation.OK or (
            self.check_in and self.check_in <= timezone.localdate()
        ):
            raise ReservationError(
                "Reservation cannot be cancelled after being used",
                ReservationErrorCode.CANCEL_NOT_ALLOWED,
            )

        self.status = Reservation.PENDING_REFUND
        self.cancellation_date = timezone.now()
        self.save()

    def mark_refunded(self):
        """Mark the reservation as refunded once the money has been returned."""
        if self.status != Reservation.PENDING_REFUND:
            raise ReservationError(
                "Reservation is not pending refund",
                ReservationErrorCode.CANCEL_NOT_ALLOWED,
            )
        self.status = Reservation.REFUNDED
        self.save()


class PaymentNotificationLog(models.Model):
    received_at = models.DateTimeField(auto_now_add=True)
    raw_parameters = models.TextField()
    signature = models.CharField(max_length=512)
    order_id = models.CharField(max_length=64, db_index=True)
    is_valid = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "payment_notification_logs"
        ordering = ["-received_at"]
