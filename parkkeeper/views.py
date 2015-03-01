# coding: utf-8

from rest_framework import viewsets
from rest_framework import generics
from rest_framework import filters
from . import models
from . import serializers


class StateViewSet(viewsets.ModelViewSet):
    queryset = models.State.objects.all()
    serializer_class = serializers.State


class CheckResults(generics.ListAPIView):
    serializer_class = serializers.CheckResult
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('check_type', )
    ordering_fields = ('dc', 'result', 'check_type')
    ordering = ('-dc', )
    paginate_by = 10
    paginate_by_param = 'page_size'
    max_paginate_by = 100

    def get_queryset(self):
        state_id = self.kwargs['state_id']
        return models.CheckResult.objects.filter(state__id=state_id).order_by('-dc')

