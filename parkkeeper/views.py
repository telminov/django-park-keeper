# coding: utf-8
from bson import CodecOptions, ObjectId
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


class WorkScheduleViewSet(rest_framework.viewsets.ReadOnlyModelViewSet):
    queryset = models.WorkSchedule.objects.all()
    serializer_class = serializers.WorkSchedule


@api_view(['GET'])
def monit_status_latest(request, format=None):
    options = CodecOptions(tz_aware=True)
    result = get_db().get_collection('monit_task', codec_options=options).aggregate(pipeline=[
        {
            '$match': {'$or': [{'cancel_dt': None}, {'cancel_dt': {'$exists': False}}]}
        },
        {
            '$group': {
                '_id': {'schedule_id': '$schedule_id', 'host_address': '$host_address'},
                'monit_name': {'$last': '$monit_name'},
                'id': {'$last': '$_id'},
                'result_dt': {'$last': '$result.dt'},
                'level': {'$last': '$result.level'},
                'extra': {'$last': '$result.extra'},
            }
        },
        {
            '$project': {
                'monit_name': 1, 'result_dt': 1, 'level': 1, 'extra': 1, 'id': 1,
                'schedule_id': '$_id.schedule_id', 'host_address': '$_id.host_address', '_id': 0
            }
        }
    ])
    status_latest = []
    for item in result:
        item['id'] = str(item['id'])
        status_latest.append(item)
    return Response({'monit_status_latest': status_latest})


@api_view(['GET'])
def work_status_latest(request, format=None):
    options = CodecOptions(tz_aware=True)
    result = get_db().get_collection('work_task', codec_options=options).aggregate(pipeline=[
        {
            '$match': {'$or': [{'cancel_dt': None}, {'cancel_dt': {'$exists': False}}]}
        },
        {
            '$group': {
                '_id': {'schedule_id': '$schedule_id', 'host_address': '$host_address'},
                'work_name': {'$last': '$work_name'},
                'id': {'$last': '$_id'},
                'result_dt': {'$last': '$result.dt'},
                'level': {'$last': '$result.level'},
                'extra': {'$last': '$result.extra'},
            }
        },
        {
            '$project': {
                'work_name': 1, 'result_dt': 1, 'level': 1, 'extra': 1, 'id': 1,
                'schedule_id': '$_id.schedule_id', 'host_address': '$_id.host_address', '_id': 0
            }
        }
    ])
    status_latest = []
    for item in result:
        item['id'] = str(item['id'])
        status_latest.append(item)
    return Response({'work_status_latest': status_latest})


@api_view(['GET'])
def monit_task(request, task_id, format=None):
    options = CodecOptions(tz_aware=True)
    task_data = get_db().get_collection('monit_task', codec_options=options).find_one({'_id': ObjectId(task_id)})
    task_data['id'] = str(task_data.pop('_id'))
    return Response(task_data)


@api_view(['GET'])
def work_task(request, task_id, format=None):
    options = CodecOptions(tz_aware=True)
    task_data = get_db().get_collection('work_task', codec_options=options).find_one({'_id': ObjectId(task_id)})
    task_data['id'] = str(task_data.pop('_id'))
    return Response(task_data)
