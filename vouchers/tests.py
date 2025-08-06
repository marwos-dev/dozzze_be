from django.contrib.auth import get_user_model
from django.test import TestCase

from reservations.models import Reservation

from .models import DiscountCoupon, Voucher

User = get_user_model()


class VoucherModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", password="pass")
        self.voucher = Voucher.objects.create(
            code="TEST",
            amount=100,
            remaining_amount=100,
            created_by=self.user,
        )

    def test_voucher_str(self):
        self.assertEqual(str(self.voucher), "TEST")

    def test_partial_redemption(self):
        self.voucher.redeem(40)
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.remaining_amount, 60)
        self.assertEqual(self.voucher.redemptions.count(), 1)

    def test_redeem_too_much(self):
        with self.assertRaises(ValueError):
            self.voucher.redeem(200)


class CouponAndReservationIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user", password="pass")
        self.voucher = Voucher.objects.create(
            code="VCH",
            amount=50,
            remaining_amount=50,
            created_by=self.user,
        )
        self.coupon = DiscountCoupon.objects.create(
            code="DISC10",
            name="Descuento 10",
            discount_percent=10,
            created_by=self.user,
        )
        self.reservation = Reservation.objects.create(total_price=100)

    def test_apply_coupon(self):
        self.reservation.apply_coupon(self.coupon)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.total_price, 90)
        self.assertEqual(self.reservation.discount_coupon, self.coupon)
        self.assertEqual(self.reservation.original_price, 100)
        self.assertEqual(self.reservation.discount_amount, 10)

    def test_apply_voucher(self):
        self.reservation.apply_voucher(self.voucher, 30)
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.remaining_amount, 20)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.total_price, 70)
        self.assertEqual(self.reservation.original_price, 100)
        self.assertEqual(self.reservation.discount_amount, 30)
        self.assertEqual(self.reservation.voucher_redemptions.count(), 1)

    def test_apply_coupon_and_voucher(self):
        self.reservation.apply_coupon(self.coupon)
        self.reservation.apply_voucher(self.voucher, 30)
        self.reservation.refresh_from_db()
        self.voucher.refresh_from_db()
        self.assertEqual(self.reservation.total_price, 60)
        self.assertEqual(self.reservation.original_price, 100)
        self.assertEqual(self.reservation.discount_amount, 40)
        self.assertEqual(self.voucher.remaining_amount, 20)
