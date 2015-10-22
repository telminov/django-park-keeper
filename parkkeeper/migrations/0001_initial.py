# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('address', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='HostGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('hosts', models.ManyToManyField(related_name='groups', to='parkkeeper.Host')),
            ],
        ),
        migrations.CreateModel(
            name='MonitSchedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('description', models.TextField(blank=True)),
                ('monit_name', models.CharField(max_length=255)),
                ('options_json', models.TextField(help_text='kwargs in json format for monitoring check', blank=True)),
                ('count', models.IntegerField(default=1)),
                ('interval', models.IntegerField(default=1)),
                ('time_units', models.CharField(max_length=50, choices=[('seconds', 'seconds'), ('minutes', 'minutes'), ('hours', 'hours'), ('days', 'days')], default='minutes')),
                ('period', models.IntegerField(editable=False, help_text='in seconds')),
                ('is_active', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(to='parkkeeper.HostGroup', blank=True)),
                ('hosts', models.ManyToManyField(to='parkkeeper.Host', blank=True)),
            ],
        ),
    ]
