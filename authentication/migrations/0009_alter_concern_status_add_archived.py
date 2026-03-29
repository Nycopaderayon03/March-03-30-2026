from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0008_add_due_warning_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="concern",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "New"),
                    ("progress", "In Progress"),
                    ("resolved", "Resolved"),
                    ("archived", "Archived"),
                ],
                default="new",
                max_length=20,
            ),
        ),
    ]

