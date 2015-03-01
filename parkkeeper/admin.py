# coding: utf-8

from django.contrib import admin
from . import models


class ShellCheckerSettingsInline(admin.TabularInline):
    model = models.ShellCheckerSettings
    extra = 1


class HttpCheckerSettingsInline(admin.TabularInline):
    model = models.HttpCheckerSettings
    extra = 1


class State(admin.ModelAdmin):
    model = models.State
    inlines = [ShellCheckerSettingsInline, HttpCheckerSettingsInline]


admin.site.register(models.State, State)