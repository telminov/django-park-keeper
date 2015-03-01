# coding: utf-8
import subprocess
from time import sleep
import requests

from django.utils import timezone

from . import models

class Checker(object):
    settings_model = None

    @classmethod
    def start(cls):
        while True:
            for checker_settings in cls.settings_model.objects.all():
                expired_dt = None

                results_qs = models.CheckResult.objects.filter(
                    state=checker_settings.state,
                    check_type=cls.settings_model.CHECK_TYPE,
                )
                if results_qs.exists():
                    last_result_dt = results_qs.latest().dc
                    expired_dt = last_result_dt + timezone.timedelta(seconds=checker_settings.period)

                if not expired_dt or expired_dt < timezone.now():
                    cls.check(checker_settings)

            sleep(1)

    @classmethod
    def _save_result(cls, checker_settings, result, description):
        check_result = models.CheckResult.objects.create(
            state=checker_settings.state,
            check_type=checker_settings.CHECK_TYPE,
            result=result,
            description=description,
        )
        return check_result


class ShellChecker(Checker):
    settings_model = models.ShellCheckerSettings

    @classmethod
    def check(cls, checker_settings):
        command = checker_settings.render_command()
        task_process = subprocess.Popen(
            command,
            shell=True,
            bufsize=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return_code = task_process.wait()
        description = task_process.stdout.read()

        if return_code == 0:
            result = models.OK_CODE
        elif return_code == 1:
            result = models.WARNING_CODE
        else:
            result = models.ERROR_CODE

        return cls._save_result(checker_settings, result, description)


class HttpChecker(Checker):
    settings_model = models.HttpCheckerSettings

    @classmethod
    def check(cls, checker_settings):
        try:
            r = requests.head(checker_settings.url)
            status_code =int(r.status_code)
            description = status_code

            if checker_settings.min_ok_status <= status_code <= checker_settings.max_ok_status:
                result = models.OK_CODE
            elif checker_settings.min_warn_status <= status_code <= checker_settings.max_warn_status:
                result = models.WARNING_CODE
            else:
                result = models.ERROR_CODE

        except requests.exceptions.ConnectionError as ex:
            result = models.ERROR_CODE
            description = unicode(ex)

        return cls._save_result(checker_settings, result, description)
