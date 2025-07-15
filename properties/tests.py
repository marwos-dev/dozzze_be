from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date

from .models import Property, Room, RoomType
from reservations.models import Reservation

User = get_user_model()


class PropertyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="owner", password="pass")
        self.property = Property.objects.create(
            owner=self.user,
            name="Test Property",
            description="Desc",
            address="Somewhere",
            location="POINT(0 0)",
        )
        self.room_type = RoomType.objects.create(property=self.property, name="Deluxe")
        self.room = Room.objects.create(property=self.property, type=self.room_type, name="Room 1", description="Desc", pax=2)

    def test_property_str(self):
        self.assertEqual(str(self.property), "Test Property")

    def test_room_str(self):
        self.assertEqual(str(self.room), "Room 1 - Test Property")

    def test_room_availability(self):
        start = date(2025, 1, 1)
        end = date(2025, 1, 2)
        Reservation.objects.create(property=self.property, check_in=start, check_out=end)
        self.room.reservations.add(Reservation.objects.first())
        self.assertFalse(self.room.is_available(start, end))


