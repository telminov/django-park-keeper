# coding: utf-8
import subprocess

from parkkeeper.monits.base import Monit, CheckResult

class PingMonit(Monit):
    @property
    def name(self):
        return 'general.ping'

    def check(self, host, **kwargs):
        result = subprocess.run(
            ['ping', host, '-c1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        success = not result.returncode
        stdout = result.stdout.decode('utf-8')
        check_result = CheckResult(host, success, extra={'stdout': stdout})

        self._save_results(check_result)
        return check_result
