import json
from datetime import timedelta
from decimal import Decimal
from typing import List

from django.db import transaction
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from ninja import Router

from pms.utils.property_helper_factory import PMSHelperFactory
from properties.models import Availability, Property
from properties.sync_service import SyncService
from utils import ErrorSchema, SuccessSchema
from utils.email_service import EmailService
from utils.error_codes import APIError, ReservationError, ReservationErrorCode
from utils.redsys import RedsysService
from vouchers.models import DiscountCoupon, Voucher

from .models import PaymentNotificationLog, Reservation, ReservationRoom
from .schemas import ReservationBatchSchema, ReservationClientOut, ReservationOut

rs = RedsysService()
router = Router(tags=["reservations"])


@router.post("/", response={200: ReservationOut, 400: ErrorSchema})
def create_reservation(request, payload: ReservationBatchSchema):
    reservations = payload.reservations
    voucher_code = payload.voucher_code
    coupon_code = payload.coupon_code
    created_reservations = []
    payable_reservations = []
    total_amount = Decimal("0.00")
    descriptions = []
    group_payment_order = rs.generate_numeric_order()

    try:
        with transaction.atomic():
            for data in reservations:
                check_in = data.check_in
                check_out = data.check_out
                room_type_id = data.room_type_id
                property_id = data.property_id
                current_date = check_in

                if check_in >= check_out:
                    raise APIError(
                        "Check-in must be before check-out",
                        ReservationErrorCode.INVALID_DATES,
                    )

                try:
                    property = Property.objects.get(id=property_id)
                except Property.DoesNotExist as exc:
                    raise APIError(
                        "Property not found",
                        ReservationErrorCode.NOT_FOUND,
                    ) from exc

                if property.pms_id:
                    helper = PMSHelperFactory().get_helper(property)
                    SyncService.sync_rates_and_availability(
                        property, helper, checkin=check_in, checkout=check_out
                    )

                while current_date < check_out:
                    availability = Availability.objects.select_for_update().get(
                        date=current_date,
                        room_type_id=room_type_id,
                        property_id=property_id,
                    )
                    if availability.availability < 1:
                        raise APIError(
                            f"No availability for room type {room_type_id} on {current_date}.",
                            ReservationErrorCode.NO_AVAILABILITY,
                        )
                    current_date += timedelta(days=1)

                current_date = check_in
                while current_date < check_out:
                    availability = Availability.objects.select_for_update().get(
                        date=current_date,
                        room_type_id=room_type_id,
                        property_id=property_id,
                    )
                    availability.availability -= 1
                    availability.save()
                    current_date += timedelta(days=1)

                reservation = Reservation.objects.create(
                    property_id=property_id,
                    check_in=check_in,
                    check_out=check_out,
                    pax_count=data.pax_count,
                    guest_name=data.guest_name,
                    guest_email=data.guest_email,
                    guest_phone=data.guest_phone,
                    guest_country=data.guest_country,
                    guest_country_iso=data.guest_country_iso,
                    guest_cp=data.guest_cp,
                    guest_city=data.guest_city,
                    guest_region=data.guest_region,
                    guest_address=data.guest_address,
                    guest_remarks=data.guest_remarks,
                    user=request.user if request.user.is_authenticated else None,
                    total_price=data.total_price,
                    paid_online=data.paid_online,
                    pay_on_arrival=data.pay_on_arrival,
                    status=Reservation.PENDING,
                    channel=data.channel,
                    payment_order=group_payment_order,  # <- todas comparten el mismo
                )

                if coupon_code and voucher_code:
                    raise APIError(
                        "Only one of voucher_code or coupon_code allowed",
                        ReservationErrorCode.INVALID_PARAMS,
                    )

                if coupon_code:
                    try:
                        coupon = DiscountCoupon.objects.get(
                            code=coupon_code, active=True
                        )
                        reservation.apply_coupon(coupon)
                        descriptions.append(f"Cupon {coupon.name} ({coupon.code})")
                    except DiscountCoupon.DoesNotExist:
                        pass

                if voucher_code:
                    try:
                        voucher = Voucher.objects.get(code=voucher_code, active=True)
                    except Voucher.DoesNotExist:
                        voucher = None

                    if voucher:
                        remaining = Decimal(str(reservation.total_price))
                        if voucher.remaining_amount >= remaining:
                            reservation.apply_voucher(voucher, remaining)
                            reservation.status = Reservation.CONFIRMED
                            reservation.payment_status = "paid"
                            reservation.save(update_fields=["status", "payment_status"])
                        else:
                            redeem_amount = voucher.remaining_amount
                            reservation.apply_voucher(voucher, redeem_amount)
                            descriptions.append(f"Voucher {voucher.code}")

                if reservation.total_price > 0:
                    payable_reservations.append(reservation)
                    total_amount += Decimal(str(reservation.total_price))

                created_reservations.append(reservation)

                ReservationRoom.objects.create(
                    reservation=reservation,
                    room_type_id=room_type_id,
                    guests=data.pax_count,
                    price=reservation.total_price,
                )

        if total_amount > 0:
            redsys_args = rs.prepare_payment_for_group(
                payable_reservations,
                total_amount,
                request,
                group_payment_order,
                description=", ".join(descriptions) if descriptions else None,
            )
            return {"success": True, "redsys_args": redsys_args}

        return {"success": True, "redsys_args": None}

    except Exception as e:
        raise APIError(
            f"An error occurred while creating the reservation(s): {str(e)}",
            ReservationErrorCode.UNKNOWN_ERROR,
        )


@csrf_exempt
@router.post("/redsys/notify/", auth=None)
def redsys_notification(request):
    try:
        merchant_parameters = request.POST.get("Ds_MerchantParameters")
        signature_received = request.POST.get("Ds_Signature")
        order_id = "unknown"

        if not merchant_parameters or not signature_received:
            PaymentNotificationLog.objects.create(
                raw_parameters=json.dumps(dict(request.POST)),
                signature=signature_received or "",
                order_id=order_id,
                is_valid=False,
                message="Missing Ds_MerchantParameters or Ds_Signature",
            )
            return {"error": "Missing parameters"}, 400

        decoded, order_id = rs.process_notification(
            merchant_parameters, signature_received
        )

        PaymentNotificationLog.objects.create(
            raw_parameters=merchant_parameters,
            signature=signature_received,
            order_id=order_id,
            is_valid=bool(decoded),
            message="Valid" if decoded else "Invalid signature or response",
        )

        if not decoded:
            raise APIError(
                "Invalid signature",
                ReservationErrorCode.PAYMENT_FAILED,
            )

        reservations = Reservation.objects.filter(payment_order=order_id)
        if not reservations.exists():
            raise APIError(
                f"No reservations found for payment_order: {order_id}",
                ReservationErrorCode.NOT_FOUND,
            )

        for reservation in reservations:
            reservation.payment_response = decoded
            reservation.payment_date = now()
            reservation.payment_status = "paid"
            reservation.status = Reservation.CONFIRMED
            reservation.save()

            if reservation.guest_email:
                EmailService.send_email(
                    subject="Reserva confirmada",
                    to_email=reservation.guest_email,
                    template_name="emails/reservation_confirmation_guest.html",
                    context={"reservation": reservation},
                )

            owner_email = getattr(reservation.property.owner, "email", None)
            if owner_email:
                EmailService.send_email(
                    subject="Nueva reserva confirmada",
                    to_email=owner_email,
                    template_name="emails/reservation_confirmation_owner.html",
                    context={"reservation": reservation},
                )

            # Notificar al PMS si lo deseas aquí

        return SuccessSchema(
            success=True,
            message="ok",
        )

    except Exception as e:
        PaymentNotificationLog.objects.create(
            raw_parameters=json.dumps(dict(request.POST)),
            signature=request.POST.get("Ds_Signature", ""),
            order_id=order_id,
            is_valid=False,
            message=str(e),
        )
        raise APIError(
            f"An error occurred while processing notification: {str(e)}",
            ReservationErrorCode.UNKNOWN_ERROR,
        )


@router.get("/my", response=List[ReservationClientOut])
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by("-created_at")
    return reservations


@router.post(
    "/{reservation_id}/cancel", response={200: SuccessSchema, 400: ErrorSchema}
)
def cancel_reservation(request, reservation_id: int):
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
    except Reservation.DoesNotExist:
        raise APIError("Reservation not found", ReservationErrorCode.NOT_FOUND)

    try:
        reservation.cancel()
    except ReservationError as e:
        raise APIError(str(e), e.code)

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

    return SuccessSchema(message="Reserva cancelada")
