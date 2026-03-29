from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0010_rename_major_gravity_to_less_grave"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sanctiontype",
            name="gravity",
            field=models.CharField(
                choices=[
                    ("Minor", "Minor"),
                    ("Less Grave", "Less Grave"),
                    ("Grave", "Grave"),
                    ("Restorative Justice", "Restorative Justice"),
                ],
                default="Minor",
                max_length=32,
            ),
        ),
    ]

