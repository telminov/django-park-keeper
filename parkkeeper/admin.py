# coding: utf-8

from django.contrib import admin
from . import models
from . import forms


class MonitSchedule(admin.ModelAdmin):
    list_display = ('monit', 'name', 'is_active')
    form = forms.MonitSchedule
admin.site.register(models.MonitSchedule, MonitSchedule)


class WorkSchedule(admin.ModelAdmin):
    list_display = ('work', 'name', 'is_active')
    form = forms.WorkSchedule
admin.site.register(models.WorkSchedule, WorkSchedule)


class Credential(admin.ModelAdmin):
    list_display = ('name', 'type', 'username')
    form = forms.Credential
admin.site.register(models.Credential, Credential)


admin.site.register(models.CredentialType)
admin.site.register(models.Host)
admin.site.register(models.HostCredential)
admin.site.register(models.HostGroup)
admin.site.register(models.WorkerType)
admin.site.register(models.Monit)
admin.site.register(models.Work)
