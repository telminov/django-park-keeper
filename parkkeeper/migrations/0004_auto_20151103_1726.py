# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkkeeper', '0003_auto_20151103_1330'),
    ]

    operations = [
        migrations.CreateModel(
            name='Credential',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('username', models.CharField(max_length=100)),
                ('encrypted_password', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='CredentialType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='HostCredential',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('credential', models.ForeignKey(to='parkkeeper.Credential')),
                ('host', models.ForeignKey(to='parkkeeper.Host')),
            ],
        ),
        migrations.AddField(
            model_name='credential',
            name='type',
            field=models.ForeignKey(to='parkkeeper.CredentialType'),
        ),
        migrations.AddField(
            model_name='monitschedule',
            name='credential_types',
            field=models.ManyToManyField(to='parkkeeper.CredentialType'),
        ),
        migrations.AlterUniqueTogether(
            name='hostcredential',
            unique_together=set([('host', 'credential')]),
        ),
    ]
