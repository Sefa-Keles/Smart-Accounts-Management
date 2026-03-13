from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("receipts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="receipt",
            name="cloudinary_public_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
