from django.test import TestCase

from .models import PMS, PMSDataResponse
from properties.models import Property
from django.contrib.auth import get_user_model

User = get_user_model()


class PMSTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="owner", password="pass")
        self.property = Property.objects.create(
            owner=self.user,
            name="Prop",
            description="Desc",
            address="Addr",
            location="POINT(0 0)",
        )
        self.pms = PMS.objects.create(name="Test PMS")

    def test_pms_str(self):
        self.assertEqual(str(self.pms), "Test PMS")

    def test_pms_data_response(self):
        resp = PMSDataResponse.objects.create(
            pms=self.pms,
            property=self.property,
            function_name="f1",
            response_data={"ok": True},
        )
        self.assertIn("ok", resp.response_data)

