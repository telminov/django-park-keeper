# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkkeeper', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Monit',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
        ),
        migrations.RemoveField(
            model_name='monitschedule',
            name='monit_name',
        ),
        migrations.AddField(
            model_name='monitschedule',
            name='monit',
            field=models.ForeignKey(to='parkkeeper.Monit', default=1),
            preserve_default=False,
        ),
    ]
