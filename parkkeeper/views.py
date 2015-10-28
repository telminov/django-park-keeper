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

