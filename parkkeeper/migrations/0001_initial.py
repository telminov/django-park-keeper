# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CheckResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('check_type', models.CharField(max_length=10, choices=[(b'shell', b'shell'), (b'http', b'http')])),
                ('result', models.IntegerField(choices=[(b'ok', 0), (b'warning', 1), (b'error', 2)])),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HttpCheckerSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period', models.IntegerField(help_text=b'seconds')),
                ('url', models.URLField()),
                ('min_ok_status', models.PositiveSmallIntegerField(help_text='minimal "ok" http status value')),
                ('max_ok_status', models.PositiveSmallIntegerField(help_text='maximum "ok" http status value')),
                ('min_warn_status', models.PositiveSmallIntegerField(help_text='minimal "warning" http status value')),
                ('max_warn_status', models.PositiveSmallIntegerField(help_text='maximum "warning" http status value')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShellCheckerSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period', models.IntegerField(help_text=b'seconds')),
                ('command_template', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('host', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='shellcheckersettings',
            name='state',
            field=models.ForeignKey(to='parkkeeper.State'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='httpcheckersettings',
            name='state',
            field=models.ForeignKey(to='parkkeeper.State'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='checkresult',
            name='state',
            field=models.ForeignKey(to='parkkeeper.State'),
            preserve_default=True,
        ),
    ]
