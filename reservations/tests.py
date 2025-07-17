from datetime import date

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from properties.models import Property, Room, RoomType
from reservations.tasks import send_check_in_reminder
from utils.error_codes import ReservationError

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


class ReservationCancellationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="owner3", password="pass")
        self.property = Property.objects.create(
            owner=self.user,
            name="Prop 3",
            description="Desc",
            address="Addr",
            location="POINT(0 0)",
        )
        self.room_type = RoomType.objects.create(property=self.property, name="Suite")
        self.reservation = Reservation.objects.create(
            property=self.property,
            check_in=timezone.localdate() + timezone.timedelta(days=10),
            check_out=timezone.localdate() + timezone.timedelta(days=12),
            guest_email="guest@example.com",
            user=self.user,
        )

    def test_cancel_reservation_sets_status_and_date(self):
        self.assertIsNone(self.reservation.cancellation_date)
        self.reservation.cancel()
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.PENDING_REFUND)
        self.assertIsNotNone(self.reservation.cancellation_date)

    def test_cannot_cancel_used_reservation(self):
        used = Reservation.objects.create(
            property=self.property,
            check_in=timezone.localdate() - timezone.timedelta(days=2),
            check_out=timezone.localdate() - timezone.timedelta(days=1),
            user=self.user,
            status=Reservation.OK,
        )

        with self.assertRaises(ReservationError):
            used.cancel()

    def test_mark_refunded_changes_status(self):
        self.reservation.cancel()
        self.reservation.mark_refunded()
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.REFUNDED)

        with self.assertRaises(ReservationError):
            self.reservation.mark_refunded()


class ReservationConfirmationEmailTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="owner4", email="owner4@example.com", password="pass"
        )
        self.property = Property.objects.create(
            owner=self.user,
            name="Prop 4",
            description="Desc",
            address="Addr",
            location="POINT(0 0)",
        )
        self.room_type = RoomType.objects.create(property=self.property, name="Suite")
        self.reservation = Reservation.objects.create(
            property=self.property,
            check_in=timezone.localdate() + timezone.timedelta(days=5),
            check_out=timezone.localdate() + timezone.timedelta(days=6),
            guest_email="guest@example.com",
        )
        self.reservation.payment_order = "123456"
        self.reservation.save()

    # def test_emails_sent_on_payment_notification(self):
    #     mail.outbox = []
    #
    #     request = HttpRequest()
    #     request.method = "POST"
    #     request.POST = QueryDict(mutable=True)
    #     request.POST.update({
    #         "Ds_MerchantParameters": "mp",
    #         "Ds_Signature": "sig"
    #     })
    #
    #     with patch.object(rs, "process_notification", return_value=({}, "123456")):
    #         redsys_notification(request)
    #
    #     self.assertEqual(len(mail.outbox), 2)
