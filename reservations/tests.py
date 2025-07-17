from datetime import date

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from properties.models import Property, Room, RoomType
from reservations.tasks import send_check_in_reminder

from .models import Reservation, ReservationRoom

User = get_user_model()


class ReservationModelTest(TestCase):
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
        self.room = Room.objects.create(
            property=self.property,
            type=self.room_type,
            name="Room 1",
            description="Desc",
            pax=2,
        )

    def test_reservation_str(self):
        reservation = Reservation.objects.create(
            property=self.property,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 2),
        )
        reservation.rooms.add(self.room)
        expected = f"Reserva en {self.room.name} del 2025-01-01 al 2025-01-02"
        self.assertEqual(str(reservation), expected)

    def test_overlapping_reservation_room(self):
        reservation1 = Reservation.objects.create(
            property=self.property,
            check_in=date(2025, 1, 1),
            check_out=date(2025, 1, 3),
        )
        ReservationRoom.objects.create(
            reservation=reservation1, room=self.room, room_type=self.room_type
        )

        reservation2 = Reservation.objects.create(
            property=self.property,
            check_in=date(2025, 1, 2),
            check_out=date(2025, 1, 4),
        )
        rr = ReservationRoom(
            reservation=reservation2,
            room=self.room,
            room_type=self.room_type,
        )
        with self.assertRaises(ValidationError):
            rr.clean()


class ReservationReminderTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="owner2", password="pass")
        self.property = Property.objects.create(
            owner=self.user,
            name="Prop 2",
            description="Desc",
            address="Addr",
            location="POINT(0 0)",
        )
        self.room_type = RoomType.objects.create(property=self.property, name="Suite")

    def test_send_reminder(self):
        check_in = timezone.localdate() + timezone.timedelta(days=7)
        reservation = Reservation.objects.create(
            property=self.property,
            check_in=check_in,
            check_out=check_in + timezone.timedelta(days=2),
            guest_email="guest@example.com",
            status=Reservation.CONFIRMED,
        )
        ReservationRoom.objects.create(
            reservation=reservation, room_type=self.room_type
        )

        mail.outbox = []
        send_check_in_reminder(7)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("guest@example.com", mail.outbox[0].to)
