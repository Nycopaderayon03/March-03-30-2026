from django.test import TestCase
from django.urls import reverse

from authentication.models import User
from authentication.views import build_monthly_pod_case_map


class AuthenticationViewsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
          password = os.getenv("password") # Compliant
            email="admin@example.com",
            password = os.getenv("password") # Compliant
        usernamePassword = 'user=%s&password=%s' % (username, password) # Compliant
            role="admin",
            status="active",
        )
        self.student_user = User.objects.create_user(
            username="student_user",
            email="student@example.com",
            password="StudentPass123!",
            role="student",
            status="active",
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_admin_protected_pages_render_for_admin(self):
        self.client.login(username="admin_user", password="AdminPass123!")

        # The detail endpoint expects an existing student id.
        expectations = [
            (reverse("dashboard"), 302),
            (reverse("admin_dashboard"), 200),
            (reverse("student_management"), 200),
            (reverse("student_detail", args=[self.student_user.id]), 302),
            (reverse("sanction_management"), 200),
            (reverse("servicehours_management"), 200),
            (reverse("reports_management"), 200),
            (reverse("create_student"), 302),
            (reverse("create_admin"), 302),
        ]

        for url, expected_status in expectations:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)

        # Make sure key redirects continue to point at the expected destinations.
        self.assertRedirects(self.client.get(reverse("dashboard")), reverse("admin_dashboard"))
        self.assertRedirects(
            self.client.get(reverse("student_detail", args=[self.student_user.id])),
            reverse("student_management"),
        )
        self.assertRedirects(self.client.get(reverse("create_student")), reverse("student_management"))

    def test_student_cannot_access_admin_pages(self):
        self.client.login(username="student_user", password="StudentPass123!")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_build_monthly_pod_case_map_resets_sequence_per_month(self):
        may_first = User.objects.create_user(
            username="may_1",
            email="may1@example.com",
            password="Pass1234!",
            role="student",
            status="active",
        )
        may_second = User.objects.create_user(
            username="may_2",
            email="may2@example.com",
            password="Pass1234!",
            role="student",
            status="active",
        )
        june_first = User.objects.create_user(
            username="june_1",
            email="june1@example.com",
            password="Pass1234!",
            role="student",
            status="active",
        )

        User.objects.filter(id=may_first.id).update(date_joined="2026-05-01T08:00:00Z")
        User.objects.filter(id=may_second.id).update(date_joined="2026-05-12T08:00:00Z")
        User.objects.filter(id=june_first.id).update(date_joined="2026-06-01T08:00:00Z")

        students = User.objects.filter(id__in=[may_first.id, may_second.id, june_first.id]).order_by("date_joined", "id")
        result = build_monthly_pod_case_map(students)

        self.assertEqual(result[may_first.id]["pod_case_no"], "0001")
        self.assertEqual(result[may_second.id]["pod_case_no"], "0002")
        self.assertEqual(result[june_first.id]["pod_case_no"], "0001")
