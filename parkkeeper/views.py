# coding: utf-8

from django.shortcuts import render
from mongoengine.connection import get_db
from rest_framework.decorators import api_view
import rest_framework.mixins
from rest_framework.response import Response
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


@api_view(['GET'])
def monit_status_latest(request, format=None):
    result = get_db().monit_task.aggregate(pipeline=[
        {
            '$match': {'$or': [{'cancel_dt': None}, {'cancel_dt': {'$exists': False}}]}
        },
        {
            '$group': {
                '_id': {'schedule_id': '$schedule_id', 'host_address': '$host_address'},
                'monit_name': {'$last': '$monit_name'},
                'result_dt': {'$last': '$result.dt'},
                'level': {'$last': '$result.level'},
                'extra': {'$last': '$result.extra'},
            }
        },
        {
            '$project': {
                'monit_name': 1, 'result_dt': 1, 'level': 1, 'extra': 1,
                'schedule_id': '$_id.schedule_id', 'host_address': '$_id.host_address', '_id': 0
            }
        }
    ])
    return Response({'monit_status_latest': result})
