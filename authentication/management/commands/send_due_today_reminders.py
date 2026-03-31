from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from authentication.models import Sanction, ServiceHourSubmission


def _format_hours(value):
    if value is None:
        return "0"
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    rounded = value.quantize(Decimal("0.01"))
    if rounded == rounded.to_integral():
        return str(int(rounded))
    return str(float(rounded))


def _build_login_url():
    base_url = (getattr(settings, "PUBLIC_BASE_URL", "") or "").strip().rstrip("/")
    path = reverse("login")
    if base_url:
        return f"{base_url}{path}"
    return path


class Command(BaseCommand):
    help = "Sends due-today reminder emails to students with remaining hours."

    def handle(self, *args, **options):
        today = timezone.localdate()
        login_url = _build_login_url()
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(
            settings, "EMAIL_HOST_USER", "no-reply@sanctiontracker.local"
        )

        sanctions = Sanction.objects.select_related("student", "sanction_type").filter(
            status="active",
            due_date=today,
            student__role="student",
        )

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for sanction in sanctions:
            if not sanction.student or not sanction.student.email:
                skipped_count += 1
                continue
            if sanction.due_warning_sent_today(today):
                skipped_count += 1
                continue

            approved_hours = (
                ServiceHourSubmission.objects.filter(
                    student=sanction.student,
                    sanction=sanction,
                    status="approved",
                ).aggregate(total=Sum("hours"))["total"]
                or Decimal("0")
            )
            required_hours = Decimal(sanction.required_hours)
            remaining_hours = max(required_hours - approved_hours, Decimal("0"))
            if remaining_hours <= Decimal("0"):
                skipped_count += 1
                continue

            subject = f'Sanction Tracker — Reminder: "{sanction.violation}" is due today'
            due_date_display = sanction.due_date.strftime("%B %d, %Y")
            body = (
                f"Hello {sanction.student.display_name},\n\n"
                f"Your sanction for \"{sanction.violation}\" is due today ({due_date_display}).\n"
                f"You still need {_format_hours(remaining_hours)} hour(s) before the sanction can be marked complete.\n\n"
                "Please submit your remaining service hours proof before the end of the day. Overdue sanctions automatically "
                "add one extra hour for each day the requirement is missed.\n\n"
                f"Log in to your account: {login_url}\n\n"
                "If you believe this is an error, contact student affairs immediately.\n"
                "Best regards,\n"
                "Student Affairs"
            )

            try:
                send_mail(subject, body, from_email, [sanction.student.email])
                sanction.record_due_warning_sent()
                sent_count += 1
            except Exception as exc:
                failed_count += 1
                self.stderr.write(
                    f"Failed to send due-today reminder to {sanction.student.email}: {exc}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Due-today reminders complete. sent={sent_count} skipped={skipped_count} failed={failed_count}"
            )
        )
