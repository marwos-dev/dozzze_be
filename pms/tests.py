from django.contrib.auth import get_user_model
from django.test import TestCase

from properties.models import Property

from .models import PMS, PMSDataResponse

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
        self.pms = PMS.objects.create(name="Test PMS", pms_key="fnsrooms")

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


class PMSHelperFactoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="owner2", password="pass")
        self.pms = PMS.objects.create(name="Factory PMS", pms_key="fnsrooms")
        self.property = Property.objects.create(
            owner=self.user,
            name="Factory Property",
            description="Desc",
            address="Addr",
            location="POINT(0 0)",
            pms=self.pms,
        )

    def test_get_helper(self):
        from pms.utils.helpers.FnsPropertyHelper import FnsPropertyHelper
        from pms.utils.property_helper_factory import PMSHelperFactory

        factory = PMSHelperFactory()
        self.assertTrue(factory.has_helper("fnsrooms"))
        helper = factory.get_helper(self.property)
        self.assertIsInstance(helper, FnsPropertyHelper)

    def test_get_helper_no_pms(self):
        from pms.utils.property_helper_factory import PMSHelperFactory

        prop = Property.objects.create(
            owner=self.user,
            name="No PMS",
            description="Desc",
            address="Addr2",
            location="POINT(0 0)",
        )

        factory = PMSHelperFactory()
        with self.assertRaises(ValueError):
            factory.get_helper(prop)


class PMSAPITest(TestCase):
    def setUp(self):
        PMS.objects.create(
            name="Integrated PMS", pms_key="fnsrooms", has_integration=True
        )
        PMS.objects.create(name="Disabled PMS", pms_key="nopms", has_integration=False)

    def test_list_pms(self):
        response = self.client.get("/api/pms/", HTTP_X_APP_KEY="clave-larga-y-unica")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Integrated PMS")
