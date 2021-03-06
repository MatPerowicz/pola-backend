# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pola', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='was_590',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='query',
            name='was_plScore',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='query',
            name='was_verified',
            field=models.BooleanField(default=False),
        ),
    ]
