import json
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import DiscountCoupon, Voucher

User = get_user_model()


class VoucherAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="owner", password="pass")
        token = AccessToken.for_user(self.user)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        self.voucher = Voucher.objects.create(
            code="VCH", amount=100, remaining_amount=80, created_by=self.user
        )
        self.coupon = DiscountCoupon.objects.create(
            code="DISC10", name="Desc 10", discount_percent=10, created_by=self.user
        )

    def test_validate_voucher(self):
        response = self.client.get(f"/api/vouchers/validate/{self.voucher.code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["type"], "voucher")
        self.assertEqual(data["redemptions"], 0)
        self.assertEqual(data["remaining_amount"], 80.0)

    def test_validate_coupon(self):
        response = self.client.get(f"/api/vouchers/validate/{self.coupon.code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["type"], "coupon")
        self.assertEqual(data["name"], self.coupon.name)
        self.assertEqual(data["discount_percent"], 10.0)

    def test_validate_invalid(self):
        response = self.client.get("/api/vouchers/validate/NOPE")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["code"], 104)
