# coding: utf-8

from rest_framework import serializers as rest_serializers
from . import models


class ShellCheckerSettings(rest_serializers.ModelSerializer):
    class Meta:
        model = models.ShellCheckerSettings

class HttpCheckerSettings(rest_serializers.ModelSerializer):
    class Meta:
        model = models.HttpCheckerSettings

class CheckResult(rest_serializers.ModelSerializer):
    class Meta:
        model = models.CheckResult


class State(rest_serializers.ModelSerializer):
    shell_checker_settings = ShellCheckerSettings(many=True, read_only=True)
    http_checker_settings = HttpCheckerSettings(many=True, read_only=True)
    class Meta:
        model = models.State