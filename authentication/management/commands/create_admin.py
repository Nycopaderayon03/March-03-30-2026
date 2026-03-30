from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = "Ensures a default admin user exists with requested credentials"

    def handle(self, *args, **options):
        admin_defaults = {
            "email": "admin@podoffice.edu",
            "role": "admin",
            "status": "active",
            "is_staff": True,
            "is_superuser": True,
            "first_name": "System",
            "last_name": "Administrator",
        }

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults=admin_defaults,
        )

        if not created:
            for field_name, field_value in admin_defaults.items():
                setattr(admin_user, field_name, field_value)

        # Enforce the requested credential for the default admin account.
        admin_user.set_password("admin123")
        admin_user.save()

        if created:
            self.stdout.write(self.style.SUCCESS("Default admin user created successfully."))
        else:
            self.stdout.write(self.style.WARNING("Admin user already existed and was updated."))
