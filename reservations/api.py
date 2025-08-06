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
    group_payment_order = rs.generate_numeric_order()

    try:
        with transaction.atomic():
            reservations = payload.reservations
            code = payload.code
            voucher = None
            coupon = None
            if code:
                try:
                    voucher = Voucher.objects.select_for_update().get(
                        code=code, active=True
                    )
                except Voucher.DoesNotExist:
                    try:
                        coupon = DiscountCoupon.objects.select_for_update().get(
                            code=code, active=True
                        )
                    except DiscountCoupon.DoesNotExist:
                        pass
            created_reservations = []
            reservation_rooms_data = []
            descriptions = []

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

                created_reservations.append(reservation)
                reservation_rooms_data.append(
                    {
                        "reservation": reservation,
                        "room_type_id": room_type_id,
                        "guests": data.pax_count,
                        "rate_id": data.rate_id,
                    }
                )

            if coupon:
                descriptions.append(f"Cupon {coupon.name} ({coupon.code})")
                for reservation in created_reservations:
                    reservation.apply_coupon(coupon)

            if voucher:
                descriptions.append(f"Voucher {voucher.code}")
                total_price = sum(
                    Decimal(str(r.total_price)) for r in created_reservations
                )
                voucher_to_apply = min(
                    Decimal(str(voucher.remaining_amount)), total_price
                )
                remaining_voucher = voucher_to_apply
                for idx, reservation in enumerate(created_reservations):
                    if remaining_voucher <= 0:
                        break
                    proportion = (
                        Decimal(str(reservation.total_price)) / total_price
                        if total_price > 0
                        else Decimal("0")
                    )
                    if idx == len(created_reservations) - 1:
                        amount = remaining_voucher
                    else:
                        amount = (voucher_to_apply * proportion).quantize(
                            Decimal("0.01")
                        )
                        if amount > remaining_voucher:
                            amount = remaining_voucher
                    if amount > 0:
                        reservation.apply_voucher(voucher, amount)
                        if reservation.total_price <= 0:
                            reservation.status = Reservation.CONFIRMED
                            reservation.payment_status = "paid"
                            reservation.save(
                                update_fields=["status", "payment_status"]
                            )
                        remaining_voucher -= amount

            payable_reservations = []
            total_amount = Decimal("0.00")
            for reservation in created_reservations:
                if reservation.total_price > 0:
                    payable_reservations.append(reservation)
                    total_amount += Decimal(str(reservation.total_price))

            for room_data in reservation_rooms_data:
                ReservationRoom.objects.create(
                    reservation=room_data["reservation"],
                    room_type_id=room_data["room_type_id"],
                    guests=room_data["guests"],
                    price=room_data["reservation"].total_price,
                    rate_id=room_data["rate_id"],
                )

            if total_amount > 0:
                redsys_args = rs.prepare_payment_for_group(
                    payable_reservations,
                    total_amount,
                    request,
                    group_payment_order,
                    description=", ".join(descriptions) if descriptions else None,
                )
                response_data = {"success": True, "redsys_args": redsys_args}
            else:
                response_data = {"success": True, "redsys_args": None}

        return response_data

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
