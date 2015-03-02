# coding: utf-8

from django.db import models
from django.template import Template, Context

OK_CODE = 0
WARNING_CODE = 1
ERROR_CODE = 2
CODE_CHOICES = (
    (OK_CODE, 'ok'),
    (WARNING_CODE, 'warning'),
    (ERROR_CODE, 'error'),
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

    def __unicode__(self):
        return self.name

    def get_status_code(self):
        # TODO
        return OK_CODE

    def get_status_name(self):
        status_code = self.get_status_code()
        return dict(CODE_CHOICES)[status_code]

class CheckResult(models.Model):
    state = models.ForeignKey(State, related_name='check_results')
    check_type = models.CharField(max_length=10, choices=TYPE_CHOICE, db_index=True)
    result = models.IntegerField(choices=CODE_CHOICES, db_index=True)
    description = models.TextField()
    dc = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        get_latest_by = 'dc'

class CheckerSettings(models.Model):
    CHECK_TYPE = None
    # state = models.ForeignKey(State)
    period = models.IntegerField(help_text='seconds')

    class Meta:
        abstract = True

class ShellCheckerSettings(CheckerSettings):
    CHECK_TYPE = SHELL_CHECK_TYPE
    state = models.ForeignKey(State, related_name='shell_checker_settings')
    command_template = models.TextField()

    def render_command(self):
        c = Context({'host': self.state.host})
        t = Template(self.command_template)
        command = t.render(c)
        return command

class HttpCheckerSettings(CheckerSettings):
    CHECK_TYPE = HTTP_CHECK_TYPE
    state = models.ForeignKey(State, related_name='http_checker_settings')
    url = models.URLField()
    min_ok_status = models.PositiveSmallIntegerField(help_text=u'minimal "ok" http status value')
    max_ok_status = models.PositiveSmallIntegerField(help_text=u'maximum "ok" http status value')
    min_warn_status = models.PositiveSmallIntegerField(help_text=u'minimal "warning" http status value')
    max_warn_status = models.PositiveSmallIntegerField(help_text=u'maximum "warning" http status value')

    def __unicode__(self):
        return self.url

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

