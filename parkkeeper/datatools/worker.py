# coding: utf-8
from parkkeeper import models


def process_worker_data(worker_data: dict) -> None:
    worker_uuid = worker_data['main']['uuid']
    if 'stop_dt' in worker_data:
        models.CurrentWorker.objects.filter(main__uuid=worker_uuid).delete()
        return

    worker = models.Worker(**worker_data['main'])

    update_params = {
        'set__main': worker,
        'set__heart_beat_dt': worker_data['heart_beat_dt'],
        'upsert': True,
    }

    if 'monits' in worker_data:
        update_params['set__monit_names'] = sorted(worker_data['monits'].keys())

    if 'works' in worker_data:
        update_params['set__work_names'] = sorted(worker_data['works'].keys())

    if 'start_task' in worker_data:
        update_params['add_to_set__task_ids'] = worker_data['start_task']['id']

    if 'complete_task' in worker_data:
        update_params['pull__task_ids'] = worker_data['complete_task']['id']

    models.CurrentWorker.objects.filter(main__uuid=worker_uuid).update(**update_params)

