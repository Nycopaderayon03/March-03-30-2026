from django.urls import reverse
from django.utils import timezone

from authentication.models import Concern, Sanction, ServiceHourSubmission


def _is_admin_user(user):
    if not getattr(user, "is_authenticated", False):
        return False
    return bool(user.is_superuser or user.is_staff or getattr(user, "role", None) == "admin")


def admin_notifications(request):
    user = getattr(request, "user", None)
    if not _is_admin_user(user):
        return {"admin_notifications": None}

    pending_submissions_qs = (
        ServiceHourSubmission.objects.filter(status="pending")
        .select_related("student", "sanction")
        .order_by("-created_at")
    )
    open_concerns_qs = (
        Concern.objects.filter(status__in=["new", "progress"])
        .select_related("student")
        .order_by("-created_at")
    )

    recent_items = []
    for submission in pending_submissions_qs[:5]:
        sanction_label = submission.sanction.violation if submission.sanction else "No sanction linked"
        recent_items.append(
            {
                "kind": "submission",
                "icon": "schedule",
                "title": f"{submission.student.display_name} submitted service hours",
                "subtitle": sanction_label,
                "created_at": submission.created_at,
                "href": reverse("servicehours_management"),
            }
        )

    for concern in open_concerns_qs[:5]:
        recent_items.append(
            {
                "kind": "concern",
                "icon": "warning",
                "title": f"{concern.student.display_name} raised a concern",
                "subtitle": concern.subject,
                "created_at": concern.created_at,
                "href": reverse("concerns_management"),
            }
        )

    recent_items.sort(key=lambda item: item["created_at"], reverse=True)
    recent_items = recent_items[:8]
    for item in recent_items:
        local_ts = timezone.localtime(item["created_at"])
        item["time_text"] = local_ts.strftime("%b %d, %I:%M %p")

    pending_count = pending_submissions_qs.count()
    concerns_count = open_concerns_qs.count()
    unread_total = pending_count + concerns_count
    return {
        "admin_notifications": {
            "unread_total": unread_total,
            "pending_submissions_count": pending_count,
            "open_concerns_count": concerns_count,
            "entries": recent_items,
        }
    }


def student_notifications(request):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False) or getattr(user, "role", None) != "student":
        return {"student_notifications": None}

    active_sanctions_qs = (
        Sanction.objects.filter(student=user, status="active")
        .select_related("sanction_type")
        .order_by("-updated_at", "-created_at")
    )
    pending_submissions_qs = (
        ServiceHourSubmission.objects.filter(student=user, status="pending")
        .select_related("sanction")
        .order_by("-created_at")
    )
    concern_updates_qs = (
        Concern.objects.filter(student=user)
        .exclude(status__in=["new", "archived"])
        .order_by("-updated_at")
    )

    entries = []
    for sanction in active_sanctions_qs[:4]:
        entries.append(
            {
                "icon": "gavel",
                "title": f"Active sanction: {sanction.violation}",
                "subtitle": f"Due {sanction.due_date.strftime('%b %d, %Y')}",
                "created_at": sanction.updated_at or sanction.created_at,
                "href": reverse("student_sanctions"),
            }
        )

    for submission in pending_submissions_qs[:4]:
        sanction_label = submission.sanction.violation if submission.sanction else "No linked sanction"
        entries.append(
            {
                "icon": "schedule",
                "title": "Service hours submission pending review",
                "subtitle": sanction_label,
                "created_at": submission.created_at,
                "href": reverse("student_service_hours"),
            }
        )

    for concern in concern_updates_qs[:4]:
        entries.append(
            {
                "icon": "forum",
                "title": f"Concern updated: {concern.status_label}",
                "subtitle": concern.subject,
                "created_at": concern.updated_at,
                "href": reverse("student_help_center"),
            }
        )

    entries.sort(key=lambda item: item["created_at"], reverse=True)
    entries = entries[:8]
    for item in entries:
        item["time_text"] = timezone.localtime(item["created_at"]).strftime("%b %d, %I:%M %p")

    sanctions_count = active_sanctions_qs.count()
    submissions_count = pending_submissions_qs.count()
    concerns_count = concern_updates_qs.count()
    unread_total = sanctions_count + submissions_count + concerns_count

    return {
        "student_notifications": {
            "unread_total": unread_total,
            "active_sanctions_count": sanctions_count,
            "pending_submissions_count": submissions_count,
            "concern_updates_count": concerns_count,
            "entries": entries,
        }
    }
