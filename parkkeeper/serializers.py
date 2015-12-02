# coding: utf-8
from rest_framework import serializers
from parkkeeper import models


class Monit(serializers.ModelSerializer):
    class Meta:
        model = models.Monit


class Work(serializers.ModelSerializer):
    class Meta:
        model = models.Work


class Host(serializers.ModelSerializer):
    class Meta:
        model = models.Host


class HostGroup(serializers.ModelSerializer):
    hosts = serializers.ManyRelatedField(Host())

    class Meta:
        model = models.HostGroup


class MonitSchedule(serializers.ModelSerializer):
    monit = Monit()
    # hosts = serializers.ManyRelatedField(Host())
    # groups = serializers.ManyRelatedField(HostGroup())
    all_hosts = serializers.SerializerMethodField()

    class Meta:
        model = models.MonitSchedule

    def get_all_hosts(self, obj):
        all_hosts_data = []
        for host in obj.get_hosts():
            all_hosts_data.append(Host(host).data)
        return all_hosts_data


class WorkSchedule(serializers.ModelSerializer):
    work = Work()
    all_hosts = serializers.SerializerMethodField()

    class Meta:
        model = models.WorkSchedule

    def get_all_hosts(self, obj):
        all_hosts_data = []
        for host in obj.get_hosts():
            all_hosts_data.append(Host(host).data)
        return all_hosts_data
