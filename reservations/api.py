import json
from datetime import timedelta
from decimal import Decimal
from typing import List

from django.db import transaction
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.errors import HttpError

from pms.utils.property_helper_factory import PMSHelperFactory
from properties.models import Availability, Property
from properties.sync_service import SyncService
from utils import ErrorSchema, SuccessSchema
from utils.redsys import RedsysService
from .models import PaymentNotificationLog, Reservation
from .schemas import ReservationOut, ReservationSchema

rs = RedsysService()
router = Router(tags=["reservations"])


@router.post("/", response={200: ReservationOut, 400: ErrorSchema})
def create_reservation(request, reservations: List[ReservationSchema]):
    created_reservations = []
    total_amount = Decimal("0.00")
    group_payment_order = rs.generate_numeric_order()

    try:
        with transaction.atomic():
            for data in reservations:
                check_in = data.check_in
                check_out = data.check_out
                room_type_id = data.room_type_id
                property_id = data.property_id
                current_date = check_in

                property = Property.objects.get(id=property_id)
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
                        raise HttpError(
                            400,
                            f"No availability for room type {room_type_id} on {current_date}.",
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

                total_amount += Decimal(data.total_price)
                created_reservations.append(reservation)

        redsys_args = rs.prepare_payment_for_group(
            created_reservations, total_amount, request, group_payment_order
        )

        return {"success": True, "redsys_args": redsys_args}

    except Exception as e:
        raise HttpError(
            400, f"An error occurred while creating the reservation(s): {str(e)}"
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
            raise HttpError(400, "Invalid signature")

        reservations = Reservation.objects.filter(payment_order=order_id)
        if not reservations.exists():
            raise HttpError(400, f"No reservations found for payment_order: {order_id}")

        for reservation in reservations:
            reservation.payment_response = decoded
            reservation.payment_date = now()
            reservation.payment_status = "paid"
            reservation.status = Reservation.CONFIRMED
            reservation.save()

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
        raise HttpError(
            400, f"An error occurred while processing notification: {str(e)}"
        )


@router.get("/my/", response=List[ReservationOut])
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by("-created_at")
    return reservations
