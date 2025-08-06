from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from reservations.models import Reservation
from utils.email_service import EmailService


@shared_task
def send_check_in_reminder(days_before: int):
    """Send reminder emails ``days_before`` days before check-in."""
    target_date = timezone.localdate() + timedelta(days=days_before)
    reservations = Reservation.objects.filter(
        check_in=target_date,
        status=Reservation.CONFIRMED,
        guest_email__isnull=False,
    )
    for reservation in reservations:
        room_types = reservation.room_types.all()
        EmailService.send_email(
            subject="Recordatorio de reserva",
            to_email=reservation.guest_email,
            template_name="emails/reservation_reminder.html",
            context={
                "reservation": reservation,
                "property": reservation.property,
                "room_types": room_types,
                "days_before": days_before,
            },
        )
    return reservations.count()


@shared_task
def send_seven_day_reminders():
    """Send reminders seven days before check-in."""
    return send_check_in_reminder(7)


@shared_task
def send_one_day_reminders():
    """Send reminders one day before check-in."""
    return send_check_in_reminder(1)
