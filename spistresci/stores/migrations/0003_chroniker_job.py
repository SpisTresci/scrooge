from django.db import migrations


def add_job(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Job = apps.get_model("chroniker", "Job")

    Job.objects.create(**{
        "name": "Update Store Products",
        "command": "update_store_offers",
        "args": "--all",
        "frequency": "HOURLY",
    })


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0002_store_last_update_revision'),
        ('chroniker', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_job),
    ]
