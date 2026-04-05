from decimal import Decimal
import time
import logging

from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from authentication.models import Sanction, ServiceHourSubmission

logger = logging.getLogger(__name__)


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
    help = "Sends due-today reminder emails to students with remaining hours (rate-limited)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            help='Number of emails to send before pausing (default: auto-detect)',
        )
        parser.add_argument(
            '--delay-between-batches',
            type=float,
            help='Delay in seconds between batches (default: auto-detect)',
        )
        parser.add_argument(
            '--delay-between-emails',
            type=float,
            help='Delay in seconds between individual emails (default: auto-detect)',
        )
        parser.add_argument(
            '--skip-bounced',
            action='store_true',
            help='Skip emails marked as bounced',
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        login_url = _build_login_url()
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or getattr(
            settings, "EMAIL_HOST_USER", "no-reply@sanctiontracker.local"
        )
        
        # Auto-detect optimal settings based on email backend
        backend = getattr(settings, 'EMAIL_BACKEND', '')
        is_resend = 'resend' in backend.lower()
        
        # Smarter defaults: Resend can handle higher load
        if is_resend:
            default_batch_size = 50
            default_delay_between_batches = 0.5
            default_delay_between_emails = 0.1
        else:
            # Gmail SMTP defaults (safer)
            default_batch_size = 10
            default_delay_between_batches = 2.0
            default_delay_between_emails = 0.5
        
        batch_size = options.get('batch_size') or default_batch_size
        delay_between_batches = options.get('delay_between_batches') or default_delay_between_batches
        delay_between_emails = options.get('delay_between_emails') or default_delay_between_emails
        skip_bounced = options.get('skip_bounced', False)

        sanctions = Sanction.objects.select_related("student", "sanction_type").filter(
            status="active",
            due_date=today,
            student__role="student",
        )

        sent_count = 0
        skipped_count = 0
        failed_count = 0
        batch_count = 0

        for sanction in sanctions:
            if not sanction.student or not sanction.student.email:
                skipped_count += 1
                continue
            
            # Skip bounced emails if flag is set
            if skip_bounced and getattr(sanction.student, 'email_bounced', False):
                skipped_count += 1
                logger.info(f"Skipping bounced email for {sanction.student.email}")
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
                batch_count += 1

                # Add delay between emails to reduce server load
                if delay_between_emails > 0:
                    time.sleep(delay_between_emails)

                # Pause between batches to prevent resource spikes
                if batch_count >= batch_size:
                    logger.info(
                        f"Email batch {sent_count // batch_size} complete. "
                        f"Pausing {delay_between_batches}s before next batch."
                    )
                    time.sleep(delay_between_batches)
                    batch_count = 0

            except Exception as exc:
                failed_count += 1
                logger.error(
                    f"Failed to send due-today reminder to {sanction.student.email}: {exc}"
                )

        elapsed_seconds = (sent_count * delay_between_emails) + ((sent_count // batch_size) * delay_between_batches)
        self.stdout.write(
            self.style.SUCCESS(
                f"Due-today reminders complete. "
                f"sent={sent_count} skipped={skipped_count} failed={failed_count} "
                f"elapsed_approx={elapsed_seconds:.1f}s"
            )
        )
        if failed_count > 0:
            logger.warning(f"Email delivery had {failed_count} failures.")
