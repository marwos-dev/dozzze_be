import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from properties.models import Availability, Property, RoomType
from reservations.models import Reservation, ReservationRoom
from vouchers.models import DiscountCoupon, Voucher

User = get_user_model()


class ReservationAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="owner", password="pass")
        token = AccessToken.for_user(self.user)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        self.property = Property.objects.create(
            owner=self.user,
            name="Prop",
            description="d",
            address="Addr",
            location="POINT(0 0)",
        )
        self.room_type = RoomType.objects.create(property=self.property, name="Deluxe")
        self.check_in = timezone.localdate() + timedelta(days=1)
        self.check_out = self.check_in + timedelta(days=1)
        Availability.objects.create(
            property=self.property,
            room_type=self.room_type,
            date=self.check_in,
            availability=2,
        )

    def _payload(self, price):
        return {
            "reservations": [
                {
                    "property_id": self.property.id,
                    "channel": "web",
                    "pax_count": 2,
                    "currency": "EUR",
                    "room_type": self.room_type.name,
                    "room_type_id": self.room_type.id,
                    "rate_id": 1,
                    "total_price": price,
                    "check_in": self.check_in.isoformat(),
                    "check_out": self.check_out.isoformat(),
                    "guest_name": "John",
                    "guest_email": "john@example.com",
                }
            ]
        }

    def _multi_payload(self, prices):
        return {
            "reservations": [
                {
                    "property_id": self.property.id,
                    "channel": "web",
                    "pax_count": 2,
                    "currency": "EUR",
                    "room_type": self.room_type.name,
                    "room_type_id": self.room_type.id,
                    "rate_id": 1,
                    "total_price": price,
                    "check_in": self.check_in.isoformat(),
                    "check_out": self.check_out.isoformat(),
                    "guest_name": "John",
                    "guest_email": "john@example.com",
                }
                for price in prices
            ]
        }

    @patch("reservations.api.SyncService.sync_rates_and_availability")
    @patch("utils.redsys.RedsysService.generate_numeric_order", return_value="0001")
    def test_create_reservation_full_voucher(self, mock_order, mock_sync):
        voucher = Voucher.objects.create(
            code="FULL",
            amount=100,
            remaining_amount=100,
            created_by=self.user,
        )
        payload = self._payload(80)
        payload["code"] = voucher.code
        with patch("utils.redsys.RedsysService.prepare_payment_for_group") as mock_pay:
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["redsys_args"])
        reservation = Reservation.objects.get()
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.CONFIRMED)
        self.assertEqual(float(reservation.total_price), 0)
        self.assertEqual(float(reservation.original_price), 80)
        self.assertEqual(float(reservation.discount_amount), 80)
        voucher.refresh_from_db()
        self.assertEqual(float(voucher.remaining_amount), 20)
        self.assertEqual(reservation.voucher_redemptions.count(), 1)
        mock_pay.assert_not_called()

    @patch("reservations.api.SyncService.sync_rates_and_availability")
    @patch("utils.redsys.RedsysService.generate_numeric_order", return_value="0002")
    def test_create_reservation_partial_voucher(self, mock_order, mock_sync):
        voucher = Voucher.objects.create(
            code="PART",
            amount=50,
            remaining_amount=50,
            created_by=self.user,
        )
        payload = self._payload(80)
        payload["code"] = voucher.code
        payment_data = {
            "endpoint": "http://pay",
            "Ds_SignatureVersion": "1",
            "Ds_MerchantParameters": "params",
            "Ds_Signature": "sig",
        }
        with patch(
            "utils.redsys.RedsysService.prepare_payment_for_group",
            return_value=payment_data,
        ) as mock_pay:
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redsys_args"], payment_data)
        reservation = Reservation.objects.get()
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.PENDING)
        self.assertEqual(float(reservation.total_price), 30)
        self.assertEqual(float(reservation.original_price), 80)
        self.assertEqual(float(reservation.discount_amount), 50)
        voucher.refresh_from_db()
        self.assertEqual(float(voucher.remaining_amount), 0)
        self.assertEqual(reservation.voucher_redemptions.count(), 1)
        mock_pay.assert_called_once()

    @patch("reservations.api.SyncService.sync_rates_and_availability")
    @patch("utils.redsys.RedsysService.generate_numeric_order", return_value="0003")
    def test_create_reservation_coupon(self, mock_order, mock_sync):
        coupon = DiscountCoupon.objects.create(
            code="DISC10",
            name="Desc 10",
            discount_percent=10,
            created_by=self.user,
        )
        payload = self._payload(100)
        payload["code"] = coupon.code
        payment_data = {
            "endpoint": "http://pay",
            "Ds_SignatureVersion": "1",
            "Ds_MerchantParameters": "params",
            "Ds_Signature": "sig",
        }
        with patch(
            "utils.redsys.RedsysService.prepare_payment_for_group",
            return_value=payment_data,
        ) as mock_pay:
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redsys_args"], payment_data)
        reservation = Reservation.objects.get()
        reservation.refresh_from_db()
        self.assertEqual(float(reservation.total_price), 90)
        self.assertEqual(float(reservation.original_price), 100)
        self.assertEqual(float(reservation.discount_amount), 10)
        self.assertEqual(reservation.discount_coupon, coupon)
        mock_pay.assert_called_once()
        list_response = self.client.get("/api/reservations/my")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()[0]["discount_coupon_code"], coupon.code)

    @patch("reservations.api.SyncService.sync_rates_and_availability")
    @patch("utils.redsys.RedsysService.generate_numeric_order", return_value="0004")
    def test_create_multiple_reservations_coupon(self, mock_order, mock_sync):
        coupon = DiscountCoupon.objects.create(
            code="DISC10",
            name="Desc 10",
            discount_percent=10,
            created_by=self.user,
        )
        payload = self._multi_payload([100, 100])
        payload["code"] = coupon.code
        payment_data = {
            "endpoint": "http://pay",
            "Ds_SignatureVersion": "1",
            "Ds_MerchantParameters": "params",
            "Ds_Signature": "sig",
        }
        with patch(
            "utils.redsys.RedsysService.prepare_payment_for_group",
            return_value=payment_data,
        ) as mock_pay:
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redsys_args"], payment_data)
        reservations = Reservation.objects.all().order_by("id")
        self.assertEqual(reservations.count(), 2)
        for r in reservations:
            r.refresh_from_db()
            self.assertEqual(float(r.total_price), 90)
            self.assertEqual(float(r.original_price), 100)
            self.assertEqual(float(r.discount_amount), 10)
            self.assertEqual(r.discount_coupon, coupon)
        mock_pay.assert_called_once()
        self.assertEqual(mock_pay.call_args[0][1], Decimal("180"))

    @patch("reservations.api.SyncService.sync_rates_and_availability")
    @patch("utils.redsys.RedsysService.generate_numeric_order", return_value="0005")
    def test_create_multiple_reservations_voucher(self, mock_order, mock_sync):
        voucher = Voucher.objects.create(
            code="VCH150",
            amount=150,
            remaining_amount=150,
            created_by=self.user,
        )
        payload = self._multi_payload([100, 100])
        payload["code"] = voucher.code
        payment_data = {
            "endpoint": "http://pay",
            "Ds_SignatureVersion": "1",
            "Ds_MerchantParameters": "params",
            "Ds_Signature": "sig",
        }
        with patch(
            "utils.redsys.RedsysService.prepare_payment_for_group",
            return_value=payment_data,
        ) as mock_pay:
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redsys_args"], payment_data)
        reservations = Reservation.objects.all().order_by("id")
        self.assertEqual(reservations.count(), 2)
        prices = [float(r.total_price) for r in reservations]
        self.assertEqual(prices, [25.0, 25.0])
        discounts = [float(r.discount_amount) for r in reservations]
        self.assertEqual(discounts, [75.0, 75.0])
        voucher.refresh_from_db()
        self.assertEqual(float(voucher.remaining_amount), 0)
        mock_pay.assert_called_once()
        self.assertEqual(mock_pay.call_args[0][1], Decimal("50"))

    @patch("reservations.api.SyncService.sync_rates_and_availability")
    @patch("utils.redsys.RedsysService.generate_numeric_order", return_value="0006")
    def test_rollback_when_failure_occurs(self, mock_order, mock_sync):
        voucher = Voucher.objects.create(
            code="FAIL",
            amount=100,
            remaining_amount=100,
            created_by=self.user,
        )
        payload = self._payload(80)
        payload["code"] = voucher.code
        with patch.object(
            ReservationRoom.objects, "create", side_effect=Exception("boom")
        ):
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Reservation.objects.count(), 0)
        voucher.refresh_from_db()
        self.assertEqual(float(voucher.remaining_amount), 100)
        availability = Availability.objects.get(
            property=self.property, room_type=self.room_type, date=self.check_in
        )
        self.assertEqual(availability.availability, 2)
