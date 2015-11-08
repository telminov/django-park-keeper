# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkkeeper', '0004_auto_20151103_1726'),
    ]

    operations = [
        migrations.AddField(
            model_name='monit',
            name='description',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='monitschedule',
            name='credential_types',
            field=models.ManyToManyField(to='parkkeeper.CredentialType', blank=True),
        ),
    ]
