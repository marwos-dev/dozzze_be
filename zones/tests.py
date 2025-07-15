from django.test import TestCase

from .models import Zone, ZoneImage


class ZoneTest(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name="Zone", description="Desc")

    def test_zone_str(self):
        self.assertEqual(str(self.zone), "Zone")

    def test_zone_image_str(self):
        img = ZoneImage.objects.create(zone=self.zone, image="path/test.jpg")
        self.assertIn(self.zone.name, str(img))
