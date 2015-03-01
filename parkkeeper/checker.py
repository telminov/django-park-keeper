# coding: utf-8
import subprocess
from django.template import Template
import requests


class ShellChecker(object):
    def check(self, checker_settings):
        context = {
            'host': checker_settings.state.host,
        }

        t = Template(self.command_template)
        command = t.render(context)

        task_process = subprocess.Popen(
            command,
            shell=True,
            bufsize=1,
            stdout=subprocess.PIPE,
        )

        return_code = task_process.wait()

        return return_code


class HttpChecker(object):
    def check(self, checker_settings):
        r = requests.head(checker_settings.url)
        return r.status_code
