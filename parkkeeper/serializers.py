# coding: utf-8
from rest_framework import serializers
from parkkeeper import models

class Host(serializers.ModelSerializer):
    class Meta:
        model = models.Host


class HostGroup(serializers.ModelSerializer):
    hosts = serializers.ManyRelatedField(Host())

    class Meta:
        model = models.HostGroup


class MonitSchedule(serializers.ModelSerializer):

    hosts = serializers.ManyRelatedField(Host())
    groups = serializers.ManyRelatedField(HostGroup())

    class Meta:
        model = models.MonitSchedule
