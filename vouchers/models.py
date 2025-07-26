from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Voucher(models.Model):
    code = models.CharField("Código", max_length=20, unique=True)
    amount = models.DecimalField("Monto original", max_digits=10, decimal_places=2)
    remaining_amount = models.DecimalField("Monto restante", max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_vouchers")
    active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vouchers"
        verbose_name = "Voucher"
        verbose_name_plural = "Vouchers"

    def __str__(self):
        return self.code

    def redeem(self, amount: float, reservation=None):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.remaining_amount:
            raise ValueError("Insufficient amount")
        self.remaining_amount -= amount
        if self.remaining_amount == 0:
            self.active = False
        self.save()
        VoucherRedemption.objects.create(
            voucher=self,
            amount=amount,
            reservation=reservation,
        )


class VoucherRedemption(models.Model):
    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.CASCADE,
        related_name="redemptions",
    )
    reservation = models.ForeignKey(
        "reservations.Reservation",
        on_delete=models.CASCADE,
        related_name="voucher_redemptions",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "voucher_redemptions"
        verbose_name = "Canjeo"
        verbose_name_plural = "Canjeos"

    def __str__(self):
        return f"{self.voucher.code} - {self.amount}"


class DiscountCoupon(models.Model):
    code = models.CharField("Código", max_length=20, unique=True)
    name = models.CharField("Nombre", max_length=50)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_coupons",
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "discount_coupons"
        verbose_name = "Cupón de descuento"
        verbose_name_plural = "Cupones de descuento"

    def __str__(self):
        return self.code
