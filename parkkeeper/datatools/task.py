# coding: utf-8
from django.utils.timezone import now
from parkkeeper import models
from parkworker.const import EXISTS_MORE_LATE_TASK_CANCEL_REASON, WORKER_DEAD_CANCEL_REASON


def cancel_double(last_task_data: dict, task_type: str) -> None:
    task_model = models.BaseTask.get_task_model(task_type)
    not_started = task_model.get_waiting_tasks().filter(
        host_address=last_task_data['host_address'],
        options=last_task_data['options'],
        dc__lt=last_task_data['dc'],
    )
    not_started.update(cancel_dt=now(), cancel_reason=EXISTS_MORE_LATE_TASK_CANCEL_REASON)


def process_task_data(data: dict) -> None:
    task_type = data['type']
    task_data = data['task']

    update_params = {}
    if task_data.get('start_dt'):
        update_params['set__start_dt'] = task_data['start_dt']

    if task_data.get('worker'):
        update_params['set__worker'] = models.Worker(**task_data['worker'])

    if task_data.get('result'):
        # print(task_data['id'], task_data['result'])
        update_params['set__result'] = models.Result(
            level=task_data['result']['level'],
            extra=task_data['result']['extra'],
            dt=task_data['result']['dt'],
        )
        cancel_double(task_data, task_type)

    if update_params:
        task_id = task_data['id']
        task_model = models.BaseTask.get_task_model(task_type)
        task_model.objects.filter(id=task_id).update(**update_params)


def cancel_dead_worker_tasks():
    current_worker_uuids = models.CurrentWorker.objects.values_list('main__uuid')

    models.MonitTask.objects\
        .filter(start_dt__ne=None, result__dt=None, cancel_dt=None,
                worker__uuid__not__in=current_worker_uuids)\
        .update(cancel_dt=now(), cancel_reason=WORKER_DEAD_CANCEL_REASON)

    models.WorkTask.objects\
        .filter(start_dt__ne=None, result__dt=None, cancel_dt=None,
                worker__uuid__not__in=current_worker_uuids)\
        .update(cancel_dt=now(), cancel_reason=WORKER_DEAD_CANCEL_REASON)

