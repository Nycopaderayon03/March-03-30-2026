"""
Test Resend email sending
Useful for verifying API key and configuration
"""
import logging
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test Resend email configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send test message to',
        )

    def handle(self, *args, **options):
        test_email = options['email']
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@resend.dev")
        
        self.stdout.write("Testing Resend email configuration...")
        self.stdout.write(f"From: {from_email}")
        self.stdout.write(f"To: {test_email}")
        self.stdout.write("")
        
        # Check if Resend is configured
        if not getattr(settings, 'RESEND_API_KEY', None):
            self.stderr.write(
                self.style.ERROR(
                    "RESEND_API_KEY not configured in .env\n"
                    "1. Sign up at https://resend.com\n"
                    "2. Get API key from settings\n"
                    "3. Add to .env: RESEND_API_KEY=re_xxxxx"
                )
            )
            return
        
        try:
            # Send test email
            result = send_mail(
                subject='Sanction Tracker - Resend Test',
                message=(
                    'Test email from Sanction Tracker using Resend API.\n\n'
                    'If you received this email, your Resend configuration is working correctly!\n\n'
                    'Configuration Summary:\n'
                    f'• From: {from_email}\n'
                    f'• Backend: {settings.EMAIL_BACKEND}\n'
                    f'• API Key: {getattr(settings, "RESEND_API_KEY", "not set")[:20]}...\n'
                ),
                from_email=from_email,
                recipient_list=[test_email],
                fail_silently=False,
            )
            
            if result == 1:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Email sent successfully!\n\n'
                        f'Check your inbox at {test_email}\n'
                        f'You can also check in Resend dashboard: https://resend.com/emails'
                    )
                )
            else:
                self.stderr.write(
                    self.style.ERROR(
                        f'Email send failed (return value: {result})'
                    )
                )
        
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f'Error sending test email:\n{str(e)}\n\n'
                    f'Common issues:\n'
                    f'1. RESEND_API_KEY not set in .env\n'
                    f'2. API key has wrong permissions\n'
                    f'3. From email not verified in Resend\n'
                    f'4. Package not installed: pip install resend'
                )
            )
            raise
