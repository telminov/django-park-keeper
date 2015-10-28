# coding: utf-8

from django.shortcuts import render
import rest_framework.mixins
import rest_framework.viewsets

from parkkeeper import models
from parkkeeper import serializers


def index(request):
    return render(request, 'index.html')


class HostViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):
    queryset = models.Host.objects.all()
    serializer_class = serializers.Host


class HostGroupViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):
    queryset = models.HostGroup.objects.all()
    serializer_class = serializers.HostGroup


class MonitScheduleViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):
    queryset = models.MonitSchedule.objects.all()
    serializer_class = serializers.MonitSchedule

