from datetime import timedelta
import json
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from unittest.mock import patch

from properties.models import Availability, Property, RoomType
from vouchers.models import Voucher, DiscountCoupon
from reservations.models import Reservation

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
            availability=1,
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
                    "total_price": price,
                    "check_in": self.check_in.isoformat(),
                    "check_out": self.check_out.isoformat(),
                    "guest_name": "John",
                    "guest_email": "john@example.com",
                }
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
        payload["voucher_code"] = voucher.code
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
        payload["voucher_code"] = voucher.code
        with patch("utils.redsys.RedsysService.prepare_payment_for_group", return_value={"ok": True}) as mock_pay:
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redsys_args"], {"ok": True})
        reservation = Reservation.objects.get()
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.PENDING)
        self.assertEqual(float(reservation.total_price), 30)
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
        payload["coupon_code"] = coupon.code
        with patch("utils.redsys.RedsysService.prepare_payment_for_group", return_value={"ok": True}) as mock_pay:
            response = self.client.post(
                "/api/reservations/",
                data=json.dumps(payload),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redsys_args"], {"ok": True})
        reservation = Reservation.objects.get()
        reservation.refresh_from_db()
        self.assertEqual(float(reservation.total_price), 90)
        self.assertEqual(reservation.discount_coupon, coupon)
        mock_pay.assert_called_once()
