# coding: utf-8

from django.db import models

OK_CODE = 0
WARNING_CODE = 1
ERROR_CODE = 2
CODE_CHOICES = (
    ('ok', OK_CODE),
    ('warning', WARNING_CODE),
    ('error', ERROR_CODE),
)

SHELL_CHECK_TYPE = 'shell'
HTTP_CHECK_TYPE = 'http'
TYPE_CHOICE = (
    (SHELL_CHECK_TYPE, SHELL_CHECK_TYPE),
    (HTTP_CHECK_TYPE, HTTP_CHECK_TYPE),
)


class State(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    host = models.CharField(max_length=100)


class CheckResult(models.Model):
    state = models.ForeignKey(State)
    check_type = models.CharField(choices=TYPE_CHOICE)
    result = models.IntegerField(choices=CODE_CHOICES)
    description = models.TextField()


class CheckerSettings(models.Model):
    CHECK_TYPE = None
    state = models.ForeignKey(State)
    period = models.IntegerField(help_text='seconds')

    class Meta:
        abstract = True

class ShellCheckerSettings(CheckerSettings):
    CHECK_TYPE = SHELL_CHECK_TYPE
    command_template = models.TextField()

class HttpCheckerSettings(CheckerSettings):
    CHECK_TYPE = HTTP_CHECK_TYPE
    url = models.URLField()
    min_ok_status = models.PositiveSmallIntegerField(help_text=u'minimal "ok" http status value')
    max_ok_status = models.PositiveSmallIntegerField(help_text=u'maximum "ok" http status value')
    min_warn_status = models.PositiveSmallIntegerField(help_text=u'minimal "warning" http status value')
    max_warn_status = models.PositiveSmallIntegerField(help_text=u'maximum "warning" http status value')


# class AnsibleChecker(CheckerSettings):
#     pass

# class ConsulChecker(CheckerSettings):
#     pass

# class MysqlChecker(CheckerSettings):
#     pass

# class MongoChecker(CheckerSettings):
#     pass

# class RabbitChecker(CheckerSettings):
#     pass

# class DockerChecker(CheckerSettings):
#     pass

