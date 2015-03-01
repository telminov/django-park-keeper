# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('parkkeeper', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='checkresult',
            options={'get_latest_by': 'dc'},
        ),
        migrations.AddField(
            model_name='checkresult',
            name='dc',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 1, 14, 37, 16, 133636), auto_now_add=True, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='checkresult',
            name='check_type',
            field=models.CharField(db_index=True, max_length=10, choices=[(b'shell', b'shell'), (b'http', b'http')]),
            preserve_default=True,
        ),
    ]
