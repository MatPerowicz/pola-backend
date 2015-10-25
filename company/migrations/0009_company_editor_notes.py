# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0008_company_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='Editor_notes',
            field=models.TextField(null=True, verbose_name='Notatki redakcji (nie pokazujemy u\u017cytkownikom)', blank=True),
        ),
    ]
