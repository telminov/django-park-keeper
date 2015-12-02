# coding: utf-8
from django.db.models.signals import post_save, post_delete, m2m_changed
from djutils.json_utils import object_to_json
from parkkeeper.models import MonitSchedule, WorkSchedule
from parkkeeper.event import emit_event
from parkkeeper.const import MONIT_SCHEDULE_EVENT, WORK_SCHEDULE_EVENT
from parkkeeper import serializers


def monit_schedule_update(sender, **kwargs):
    instance = kwargs['instance']
    created = kwargs.get('created', False)
    instance_data = serializers.MonitSchedule(instance).data
    event = {
        'instance': instance_data,
        'event': 'create' if created else 'update',
    }
    event_json = object_to_json(event)
    emit_event(MONIT_SCHEDULE_EVENT, event_json)

post_save.connect(monit_schedule_update, sender=MonitSchedule)
m2m_changed.connect(monit_schedule_update, sender=MonitSchedule.hosts.through)
m2m_changed.connect(monit_schedule_update, sender=MonitSchedule.groups.through)
m2m_changed.connect(monit_schedule_update, sender=MonitSchedule.credential_types.through)


def monit_schedule_delete(sender, **kwargs):
    instance = kwargs['instance']
    instance_data = serializers.MonitSchedule(instance).data
    event = {
        'instance': instance_data,
        'event': 'delete',
    }
    event_json = object_to_json(event)
    emit_event(MONIT_SCHEDULE_EVENT, event_json)

post_delete.connect(monit_schedule_delete, sender=MonitSchedule)


def work_schedule_update(sender, **kwargs):
    instance = kwargs['instance']
    created = kwargs.get('created', False)
    instance_data = serializers.WorkSchedule(instance).data
    event = {
        'instance': instance_data,
        'event': 'create' if created else 'update',
    }
    event_json = object_to_json(event)
    emit_event(WORK_SCHEDULE_EVENT, event_json)

post_save.connect(work_schedule_update, sender=WorkSchedule)
m2m_changed.connect(work_schedule_update, sender=WorkSchedule.hosts.through)
m2m_changed.connect(work_schedule_update, sender=WorkSchedule.groups.through)
m2m_changed.connect(work_schedule_update, sender=WorkSchedule.credential_types.through)


def work_schedule_delete(sender, **kwargs):
    instance = kwargs['instance']
    instance_data = serializers.WorkSchedule(instance).data
    event = {
        'instance': instance_data,
        'event': 'delete',
    }
    event_json = object_to_json(event)
    emit_event(WORK_SCHEDULE_EVENT, event_json)

post_delete.connect(work_schedule_delete, sender=WorkSchedule)
