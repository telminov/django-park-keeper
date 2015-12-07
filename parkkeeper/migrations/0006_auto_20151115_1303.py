# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkkeeper', '0005_auto_20151108_1008'),
    ]

    operations = [
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField()),
                ('worker_type', models.ForeignKey(to='parkkeeper.WorkerType')),
            ],
        ),
        migrations.CreateModel(
            name='WorkSchedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('options_json', models.TextField(help_text='kwargs in json format for task', blank=True)),
                ('count', models.IntegerField(default=1)),
                ('interval', models.IntegerField(default=1)),
                ('time_units', models.CharField(default='minutes', choices=[('seconds', 'seconds'), ('minutes', 'minutes'), ('hours', 'hours'), ('days', 'days')], max_length=50)),
                ('period', models.IntegerField(help_text='in seconds', editable=False)),
                ('is_active', models.BooleanField(default=True)),
                ('credential_types', models.ManyToManyField(blank=True, to='parkkeeper.CredentialType')),
                ('groups', models.ManyToManyField(blank=True, to='parkkeeper.HostGroup')),
                ('hosts', models.ManyToManyField(blank=True, to='parkkeeper.Host')),
                ('work', models.ForeignKey(to='parkkeeper.Work')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='monitschedule',
            name='options_json',
            field=models.TextField(help_text='kwargs in json format for task', blank=True),
        ),
    ]
