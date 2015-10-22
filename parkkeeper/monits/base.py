# coding: utf-8
from abc import ABCMeta, abstractmethod, abstractproperty
import datetime


class Monit(metaclass=ABCMeta):
    @staticmethod
    def get_monit(name: str) -> 'Monit':
        # TODO
        import parkkeeper.monits.general
        return parkkeeper.monits.general.PingMonit()

    @abstractproperty
    def name(self):
        pass

    @property
    def description(self):
        return ''

    @abstractmethod
    def check(self, host: str, **kwargs) -> 'CheckResult':
        pass

    def _save_results(self, result: 'CheckResult'):
        # TODO
        pass


class CheckResult:
    def __init__(self, host: str, success: bool, dt: datetime.datetime=None, extra: dict=None):
        self.host = host
        self.success = success
        self.dt = dt or datetime.datetime.now()
        self.extra = extra
