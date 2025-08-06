from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.text import slugify
from rest_framework_simplejwt.tokens import AccessToken

from pms.models import PMS
from reservations.models import Reservation
from zones.models import Zone

from .models import Property, Room, RoomType, Service

User = get_user_model()


class PropertyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="owner", password="pass")
        self.pms = PMS.objects.create(name="Test PMS", pms_key="fnsrooms")
        self.property = Property.objects.create(
            owner=self.user,
            name="Test Property",
            description="Desc",
            address="Somewhere",
            location="POINT(0 0)",
            pms=self.pms,
        )
        self.room_type = RoomType.objects.create(property=self.property, name="Deluxe")
        self.room = Room.objects.create(
            property=self.property,
            type=self.room_type,
            name="Room 1",
            description="Desc",
            pax=2,
        )

    def test_property_str(self):
        self.assertEqual(str(self.property), "Test Property")

    def test_room_str(self):
        self.assertEqual(str(self.room), "Room 1 - Test Property")

    def test_room_availability(self):
        start = date(2025, 1, 1)
        end = date(2025, 1, 2)
        Reservation.objects.create(
            property=self.property, check_in=start, check_out=end
        )
        self.room.reservations.add(Reservation.objects.first())
        self.assertFalse(self.room.is_available(start, end))


class PropertyAPITest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff",
            password="pass",
            is_staff=True,
        )
        self.zone = Zone.objects.create(name="Zone", description="desc")
        self.pms = PMS.objects.create(name="Test PMS", pms_key="fnsrooms")
        self.property = Property.objects.create(
            owner=self.staff,
            name="APITestProp",
            description="Desc",
            address="Somewhere",
            location="POINT(0 0)",
            pms=self.pms,
            zone=self.zone,
        )
        token = AccessToken.for_user(self.staff)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def test_list_my_properties(self):
        response = self.client.get("/api/properties/my/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.property.id)

    def test_create_property(self):
        payload = {
            "name": "New Prop",
            "description": "d",
            "address": "addr",
            "latitude": 0.0,
            "longitude": 0.0,
        }
        response = self.client.post(
            "/api/properties/my/",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Property.objects.count(), 2)

    def test_create_property_invalid_zone(self):
        payload = {
            "name": "Bad",
            "description": "d",
            "address": "addr2",
            "latitude": 0.0,
            "longitude": 0.0,
            "zone_id": 9999,
        }
        response = self.client.post(
            "/api/properties/my/",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_create_property_invalid_pms(self):
        payload = {
            "name": "BadPMS",
            "description": "d",
            "address": "addr3",
            "latitude": 0.0,
            "longitude": 0.0,
            "pms_id": 9999,
        }
        response = self.client.post(
            "/api/properties/my/",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_create_property_duplicate(self):
        payload = {
            "name": "APITestProp",
            "description": "Desc",
            "address": "Somewhere",
            "latitude": 0.0,
            "longitude": 0.0,
        }
        response = self.client.post(
            "/api/properties/my/",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    # def test_sync_property(self):
    #     pms_data = PmsDataProperty.objects.create(
    #         property=self.property,
    #
    #     )
    #     with patch(
    #         "properties.api.SyncService.sync_property_detail", return_value=True
    #     ), patch(
    #         "properties.api.SyncService.sync_rooms", return_value=True
    #     ), patch(
    #         "properties.api.SyncService.sync_reservations", return_value=True
    #     ), patch(
    #         "properties.api.SyncService.sync_rates_and_availability", return_value=True
    #     ):
    #         response = self.client.post(f"/api/properties/my/{self.property.id}/sync")
    #         print("response", response.json())
    #         self.assertEqual(response.status_code, 200)
    #         self.assertIn("message", response.json())
    #     pms_data.refresh_from_db()
    #     self.assertFalse(pms_data.first_sync)

    def test_update_property_invalid_zone(self):
        payload = {"zone_id": 9999}
        response = self.client.put(
            f"/api/properties/my/{self.property.id}",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_update_property_duplicate(self):
        other = Property.objects.create(
            owner=self.staff,
            name="Other",
            description="d",
            address="Addr",
            location="POINT(0 0)",
            zone=self.zone,
            pms=self.pms,
        )
        payload = {"name": other.name, "address": other.address}
        response = self.client.put(
            f"/api/properties/my/{self.property.id}",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_get_property_by_name(self):
        slug = slugify(self.property.name)
        response = self.client.get(f"/api/properties/name/{slug}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.property.id)
        self.assertEqual(data["name"], self.property.name)

    def test_update_room_type_success(self):
        room_type = RoomType.objects.create(property=self.property, name="Old")
        payload = {"name": "New", "description": "Updated"}
        response = self.client.put(
            f"/api/properties/my/room-types/{room_type.id}",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        room_type.refresh_from_db()
        self.assertEqual(room_type.name, "New")
        self.assertEqual(room_type.description, "Updated")

    def test_update_room_type_not_found(self):
        other_user = User.objects.create_user(
            username="other", password="pass", is_staff=True
        )
        other_prop = Property.objects.create(
            owner=other_user,
            name="OtherProp",
            description="d",
            address="Addr",
            location="POINT(0 0)",
        )
        other_rt = RoomType.objects.create(property=other_prop, name="Type")
        payload = {"name": "New"}
        response = self.client.put(
            f"/api/properties/my/room-types/{other_rt.id}",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_update_room_type_access_denied(self):
        rt = RoomType.objects.create(property=self.property, name="Old")
        user = User.objects.create_user(username="u", password="pass")
        token = AccessToken.for_user(user)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        response = self.client.put(
            f"/api/properties/my/room-types/{rt.id}",
            data={"name": "N"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_property_service_crud(self):
        payload = {"code": "wifi", "name": "Wifi", "description": "Fast"}
        response = self.client.post(
            f"/api/properties/my/{self.property.id}/services",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        service_id = response.json()["id"]

        response = self.client.get(
            f"/api/properties/my/{self.property.id}/services"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "wifi")

        update_payload = {"description": "Super fast"}
        response = self.client.put(
            f"/api/properties/my/{self.property.id}/services/{service_id}",
            data=update_payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["description"], "Super fast")

        response = self.client.delete(
            f"/api/properties/my/{self.property.id}/services/{service_id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Service.objects.count(), 0)

    def test_room_type_inherits_property_services(self):
        service = Service.objects.create(code="ac", name="A/C", description="Cool")
        self.property.services.add(service)
        rt = RoomType.objects.create(property=self.property, name="Suite")
        response = self.client.get(f"/api/properties/rooms/{rt.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("services", data)
        codes = [s["code"] for s in data["services"]]
        self.assertIn(service.code, codes)

    def test_list_service_catalog(self):
        Service.objects.create(code="wifi", name="Wifi", description="Fast")
        Service.objects.create(code="ac", name="A/C", description="Cool")
        response = self.client.get("/api/properties/services")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        codes = {s["code"] for s in data}
        self.assertIn("wifi", codes)
        self.assertIn("ac", codes)
