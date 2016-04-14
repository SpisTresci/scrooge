# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-13 23:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='Store name')),
                ('url', models.URLField(verbose_name='Store url address')),
            ],
        ),
    ]
