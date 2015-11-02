# coding: utf-8

from django.contrib import admin
from . import models
from . import forms


class MonitSchedule(admin.ModelAdmin):
    list_display = ('monit', 'name', 'is_active')
    form = forms.MonitSchedule

admin.site.register(models.MonitSchedule, MonitSchedule)
admin.site.register(models.Host)
admin.site.register(models.HostGroup)
admin.site.register(models.Monit)
