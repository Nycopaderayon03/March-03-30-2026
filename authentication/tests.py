from django.test import TestCase
from django.urls import reverse

from authentication.models import Sanction, SanctionType, User
from authentication.views import build_monthly_pod_case_map


class AuthenticationViewsTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password="AdminPass123!",
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
            (reverse("student_detail", args=[self.student_user.id]), 200),
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
        self.assertRedirects(self.client.get(reverse("create_student")), reverse("student_management"))

    def test_student_cannot_access_admin_pages(self):
        self.client.login(username="student_user", password="StudentPass123!")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_add_new_student_first_offense_creates_offense_only_record(self):
        self.client.login(username="admin_user", password="AdminPass123!")
        SanctionType.objects.create(description="Long Hair", gravity="Minor")

        response = self.client.post(
            reverse("add_new_student_with_sanction"),
            {
                "new_student_id": "STU-2001",
                "full_name": "First Offense",
                "new_student_email": "first.offense@example.com",
                "course_year": "BSSC-1",
                "new_student_department": "Bachelor of Science in Information Technology",
                "new_sanction_flow": "first_offense",
                "new_violation": "Long Hair",
                "new_required_hours": "",
                "new_note": "Hair length violation",
                "new_date_issued": "2026-04-16",
                "new_due_date": "2026-04-20",
            },
        )
        self.assertEqual(response.status_code, 302)

        student = User.objects.get(student_code="STU-2001")
        sanction = Sanction.objects.get(student=student)
        self.assertEqual(sanction.sanction_flow, "first_offense")
        self.assertEqual(sanction.required_hours, 0)
        self.assertFalse(student.has_usable_password())

    def test_add_new_student_community_service_creates_portal_access(self):
        self.client.login(username="admin_user", password="AdminPass123!")
        SanctionType.objects.create(description="Littering", gravity="Minor")

        response = self.client.post(
            reverse("add_new_student_with_sanction"),
            {
                "new_student_id": "STU-2002",
                "full_name": "Community Service",
                "new_student_email": "community.service@example.com",
                "course_year": "BSSC-1",
                "new_student_department": "Bachelor of Science in Information Technology",
                "new_sanction_flow": "community_service",
                "new_violation": "Littering",
                "new_required_hours": "5",
                "new_note": "Community service required",
                "new_date_issued": "2026-04-16",
                "new_due_date": "2026-04-25",
            },
        )
        self.assertEqual(response.status_code, 302)

        student = User.objects.get(student_code="STU-2002")
        sanction = Sanction.objects.get(student=student)
        self.assertEqual(sanction.sanction_flow, "community_service")
        self.assertEqual(sanction.required_hours, 5)
        self.assertTrue(student.has_usable_password())
        self.assertTrue(student.check_password("STU-2002"))

    def test_student_management_case_filter(self):
        self.client.login(username="admin_user", password="AdminPass123!")
        SanctionType.objects.create(description="Uniform", gravity="Minor")

        first_student = User.objects.create_user(
            username="first_case",
            email="first.case@example.com",
            password="Pass1234!",
            role="student",
            status="active",
            student_code="STU-3001",
        )
        service_student = User.objects.create_user(
            username="service_case",
            email="service.case@example.com",
            password="Pass1234!",
            role="student",
            status="active",
            student_code="STU-3002",
        )

        Sanction.objects.create(
            student=first_student,
            sanction_type=SanctionType.objects.get(description="Uniform"),
            violation_snapshot="Uniform",
            sanction_flow="first_offense",
            required_hours=0,
            date_issued="2026-04-16",
            due_date="2026-04-20",
        )
        Sanction.objects.create(
            student=service_student,
            sanction_type=SanctionType.objects.get(description="Uniform"),
            violation_snapshot="Uniform",
            sanction_flow="community_service",
            required_hours=4,
            date_issued="2026-04-16",
            due_date="2026-04-20",
        )

        first_response = self.client.get(reverse("student_management"), {"case_filter": "first_offense"})
        self.assertContains(first_response, "STU-3001")
        self.assertNotContains(first_response, "STU-3002")

        service_response = self.client.get(reverse("student_management"), {"case_filter": "community_service"})
        self.assertContains(service_response, "STU-3002")
        self.assertNotContains(service_response, "STU-3001")

    def test_admin_can_resolve_offense_sanction(self):
        self.client.login(username="admin_user", password="AdminPass123!")
        sanction_type = SanctionType.objects.create(description="Hair", gravity="Minor")
        sanction = Sanction.objects.create(
            student=self.student_user,
            sanction_type=sanction_type,
            violation_snapshot="Hair",
            sanction_flow="first_offense",
            required_hours=0,
            status="active",
            date_issued="2026-04-16",
            due_date="2026-04-20",
        )

        response = self.client.post(reverse("resolve_offense_sanction", args=[sanction.id]))
        self.assertEqual(response.status_code, 302)
        sanction.refresh_from_db()
        self.assertEqual(sanction.status, "completed")

    def test_admin_cannot_resolve_community_service_sanction(self):
        self.client.login(username="admin_user", password="AdminPass123!")
        sanction_type = SanctionType.objects.create(description="Service", gravity="Minor")
        sanction = Sanction.objects.create(
            student=self.student_user,
            sanction_type=sanction_type,
            violation_snapshot="Service",
            sanction_flow="community_service",
            required_hours=5,
            status="active",
            date_issued="2026-04-16",
            due_date="2026-04-25",
        )

        response = self.client.post(reverse("resolve_offense_sanction", args=[sanction.id]))
        self.assertEqual(response.status_code, 302)
        sanction.refresh_from_db()
        self.assertEqual(sanction.status, "active")

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


class JwtAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jwt_user",
            email="jwt@example.com",
            password="JwtPass123!",
            role="student",
            status="active",
            student_code="STU-1001",
        )

    def test_obtain_token_and_access_me_endpoint(self):
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "jwt_user", "password": "JwtPass123!"},
            content_type="application/json",
        )
        self.assertEqual(token_response.status_code, 200)
        payload = token_response.json()
        self.assertIn("access", payload)
        self.assertIn("refresh", payload)
        self.assertEqual(payload["user"]["username"], "jwt_user")

        me_response = self.client.get(
            reverse("api_me"),
            HTTP_AUTHORIZATION=f"Bearer {payload['access']}",
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["email"], "jwt@example.com")

    def test_inactive_status_user_cannot_get_token(self):
        self.user.status = "inactive"
        self.user.save(update_fields=["status"])

        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "jwt_user", "password": "JwtPass123!"},
            content_type="application/json",
        )
        self.assertEqual(token_response.status_code, 400)
