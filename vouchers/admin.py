from django.contrib import admin

from .models import DiscountCoupon, Voucher, VoucherRedemption


class VoucherRedemptionInline(admin.TabularInline):
    model = VoucherRedemption
    readonly_fields = ("amount", "redeemed_at")
    extra = 0
    can_delete = False


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "amount",
        "remaining_amount",
        "active",
        "created_by",
        "created_at",
    )
    search_fields = ("code",)
    readonly_fields = ("created_by", "remaining_amount")
    inlines = [VoucherRedemptionInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.remaining_amount = obj.amount
        super().save_model(request, obj, form, change)


@admin.register(DiscountCoupon)
class DiscountCouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "discount_percent",
        "active",
        "created_by",
        "created_at",
    )
    search_fields = ("code", "name")
    readonly_fields = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
