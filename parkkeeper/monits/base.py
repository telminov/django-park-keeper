# coding: utf-8
from abc import ABCMeta, abstractmethod
import datetime
import os
from typing import Dict
import sys

from django.conf import settings
from parkkeeper import models


class DuplicatedMonitNameException(Exception):
    pass

class Monit(metaclass=ABCMeta):
    name = None
    description = None

    @abstractmethod
    def check(self, host: str, **kwargs) -> models.CheckResult:
        pass

    @classmethod
    def get_monit(cls, name: str) -> 'Monit':
        monits = cls.get_all_monits()
        for monit_name, monit_module in monits:
            if name == monit_name:
                return monit_module

    @classmethod
    def get_all_monits(cls) -> Dict[str, 'Monit']:
        if not hasattr(cls, '_monits'):
            monits = {}

            for app_name in settings.INSTALLED_APPS:
                app_module = __import__(app_name)

                if not os.path.isdir(app_module.__path__[0] + '/monits'):
                    continue

                for module_path in os.listdir(app_module.__path__[0] + '/monits'):
                    if not module_path.endswith('.py'):
                        continue

                    module_name = os.path.splitext(module_path)[0]
                    module_full_name = '%s.monits.%s' % (app_name, module_name)
                    __import__(module_full_name)
                    monit_module = sys.modules[module_full_name]
                    for module_item in monit_module.__dict__.values():
                        if type(module_item) is ABCMeta \
                                and issubclass(module_item, Monit) \
                                and module_item is not Monit:
                            monits.setdefault(module_item.name, []).append(module_item)

            # check no duplicated names
            for monit_name, monit_modules in monits.items():
                if len(monit_modules) > 1:
                    raise DuplicatedMonitNameException('Modules %s have same name "%s"' % (
                        ' and '.join(map(str, monit_modules)),
                        monit_name
                    ))

            # create immutable list of modules
            cls._monits = tuple([(monit_name, monit_modules[0]) for monit_name, monit_modules in monits.items()])

        return cls._monits

