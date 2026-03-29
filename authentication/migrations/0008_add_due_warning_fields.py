from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0007_sync_sanction_schema"),
    ]

    operations = [
        migrations.AddField(
            model_name="sanction",
            name="due_warning_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sanction",
            name="last_overdue_extension_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
