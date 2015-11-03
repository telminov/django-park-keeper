# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkkeeper', '0002_auto_20151102_1401'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkerType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('port', models.IntegerField()),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='monit',
            name='worker_type',
            field=models.ForeignKey(default=1, to='parkkeeper.WorkerType'),
            preserve_default=False,
        ),
    ]
