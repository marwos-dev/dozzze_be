# reservations/redsys_service.py
import base64
import hashlib
import hmac
import json
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from redsys.client import RedirectClient
from redsys.constants import EUR, STANDARD_PAYMENT


class RedsysService:
    def __init__(self):
        self.client = RedirectClient(settings.REDSYS_SECRET_KEY)
        self.endpoint = settings.REDSYS_URL

    def prepare_payment(self, reservation, request):
        amount = Decimal(str(reservation.total_price)).quantize(Decimal('.01'), ROUND_HALF_UP)
        order = reservation.payment_order or str(reservation.id).zfill(12)

        params = {
            "merchant_code": settings.REDSYS_MERCHANT_CODE,
            "terminal": settings.REDSYS_TERMINAL,
            "transaction_type": STANDARD_PAYMENT,
            "currency": EUR,
            "order": order,
            "amount": amount,
            "merchant_data": f"res_id={reservation.id}",
            # "merchant_name": settings.REDSYS_MERCHANT_NAME,
            "titular": reservation.guest_name or reservation.guest_corporate or "Guest",
            "product_description": f"Reserva #{reservation.id}",
            "merchant_url": f"{settings.BACKEND_URL}/api/reservations/redsys/notify/",
            "url_ok": f"{settings.FRONTEND_URL}/reserve/ok?order={order}&amount={amount}&currency={reservation.currency}",
            "url_ko": f"{settings.FRONTEND_URL}/reserve/failed",
        }

        args = self.client.prepare_request(params)
        reservation.payment_order = order
        reservation.payment_amount = int(amount * 100)
        reservation.payment_signature = args["Ds_Signature"]
        reservation.save(update_fields=["payment_order", "payment_amount", "payment_signature"])
        return {
            "endpoint": self.endpoint,
            "Ds_SignatureVersion": args["Ds_SignatureVersion"],
            "Ds_MerchantParameters": args["Ds_MerchantParameters"],
            "Ds_Signature": args["Ds_Signature"],
        }

    def process_notification(self, merchant_parameters, signature_received):
        try:

            # Decode parameters
            decoded = json.loads(base64.b64decode(merchant_parameters).decode())
            order_id = decoded["Ds_Order"]
            response_code = int(decoded["Ds_Response"])

            resp = self.client.create_response(signature_received, merchant_parameters)
            if not resp.is_authorized:
                return False, "Firma no válida"

            if resp.is_canceled:
                return False, "Pago cancelado por el usuario"

            if resp.is_refunded:
                return False, "Pago reembolsado"

            if resp.is_paid:
                return decoded, order_id

            return False, f"Pago fallido con código de respuesta: {response_code}"

        except Exception as e:
            return False, f"Error al procesar la notificación: {str(e)}"


    def prepare_payment_for_group(self, reservations, total_amount, request, group_payment_order):
        titular = reservations[0].guest_name or reservations[0].guest_corporate or "Guest"
        property_currency = getattr(reservations[0], "currency", "978")  # EUR por defecto

        amount = Decimal(str(total_amount)).quantize(Decimal('.01'), ROUND_HALF_UP)

        params = {
            "merchant_code": settings.REDSYS_MERCHANT_CODE,
            "terminal": settings.REDSYS_TERMINAL,
            "transaction_type": STANDARD_PAYMENT,
            "currency": property_currency,
            "order": group_payment_order,
            "amount": amount,
            "merchant_data": f"group={group_payment_order}",
            "titular": titular,
            "product_description": f"Reservas múltiples #{group_payment_order}",
            "merchant_url": f"{settings.BACKEND_URL}/api/reservations/redsys/notify/",
            "url_ok": f"{settings.FRONTEND_URL}/reserve/ok?order={group_payment_order}&amount={amount}&currency={property_currency}",
            "url_ko": f"{settings.FRONTEND_URL}/reserve/failed",
        }

        args = self.client.prepare_request(params)
        for res in reservations:
            res.payment_order = group_payment_order
            res.payment_amount = int(amount * 100)
            res.payment_signature = args["Ds_Signature"]
            res.save(update_fields=["payment_order", "payment_amount", "payment_signature"])

        return {
            "endpoint": self.endpoint,
            "Ds_SignatureVersion": args["Ds_SignatureVersion"],
            "Ds_MerchantParameters": args["Ds_MerchantParameters"],
            "Ds_Signature": args["Ds_Signature"],
        }
