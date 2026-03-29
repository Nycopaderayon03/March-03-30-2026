from django.db import migrations, models


def rename_major_to_less_grave(apps, schema_editor):
    SanctionType = apps.get_model("authentication", "SanctionType")
    SanctionType.objects.filter(gravity="Major").update(gravity="Less Grave")


def revert_less_grave_to_major(apps, schema_editor):
    SanctionType = apps.get_model("authentication", "SanctionType")
    SanctionType.objects.filter(gravity="Less Grave").update(gravity="Major")


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0009_alter_concern_status_add_archived"),
    ]

    operations = [
        migrations.RunPython(rename_major_to_less_grave, revert_less_grave_to_major),
        migrations.AlterField(
            model_name="sanctiontype",
            name="gravity",
            field=models.CharField(
                choices=[("Minor", "Minor"), ("Less Grave", "Less Grave"), ("Grave", "Grave")],
                default="Minor",
                max_length=10,
            ),
        ),
    ]

