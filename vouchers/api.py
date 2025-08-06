from ninja import Router

from utils import ErrorSchema
from utils.error_codes import ReservationErrorCode

from .models import DiscountCoupon, Voucher
from .schemas import CodeValidationOut

router = Router(tags=["vouchers"])


@router.get("/validate/{code}", response={200: CodeValidationOut, 404: ErrorSchema})
def validate_code(request, code: str):
    try:
        voucher = Voucher.objects.get(code=code)
        return {
            "type": "voucher",
            "applicable": voucher.active,
            "redemptions": voucher.redemptions.count(),
            "remaining_amount": float(voucher.remaining_amount),
        }
    except Voucher.DoesNotExist:
        try:
            coupon = DiscountCoupon.objects.get(code=code)
            return {
                "type": "coupon",
                "applicable": coupon.active,
                "name": coupon.name,
                "discount_percent": float(coupon.discount_percent),
            }
        except DiscountCoupon.DoesNotExist:
            return 404, {
                "detail": "Code not found",
                "code": int(ReservationErrorCode.NOT_FOUND),
                "status_code": 404,
            }
