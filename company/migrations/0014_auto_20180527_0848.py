# Generated by Django 2.0.3 on 2018-05-27 06:48

import django.contrib.postgres.indexes
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0013_auto_20171207_0122'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='company',
            index=django.contrib.postgres.indexes.BrinIndex(
                fields=['created_at'], name='company_com_created_54f6ef_brin', pages_per_range=16
            ),
        ),
    ]
