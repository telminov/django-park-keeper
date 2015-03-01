# coding: utf-8

from rest_framework import viewsets
from . import models
from . import serializers

class StateViewSet(viewsets.ModelViewSet):
    queryset = models.State.objects.all()
    serializer_class = serializers.State