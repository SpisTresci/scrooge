# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-08 20:01
from __future__ import unicode_literals

from django.db import migrations


def redefine_default_job(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Job = apps.get_model("chroniker", "Job")

    jobs = Job.objects.filter(**{
        "command": "update_store_products",
    })

    for job in jobs:
        job.raw_command = "cd /app/ && python manage.py update_store_offers {}".format(job.args)
        job.command = ""
        job.args = ""
        job.save()


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0008_auto_20160607_0029'),
        ('offers', '0002_auto_20160606_2315'),
    ]

    operations = [
        migrations.RunPython(redefine_default_job),
    ]
