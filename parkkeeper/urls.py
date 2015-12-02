# coding: utf-8
from django.conf.urls import url, patterns
from rest_framework import routers
from parkkeeper import views
from rest_framework.urlpatterns import format_suffix_patterns

router = routers.DefaultRouter()
router.register('host', views.HostViewSet)
router.register('host_group', views.HostGroupViewSet)
router.register('monit_schedule', views.MonitScheduleViewSet)
router.register('work_schedule', views.WorkScheduleViewSet)


urlpatterns = [
    url(r'^$', views.index),
    url(r'^monit_status_latest/$', views.monit_status_latest),
    url(r'^work_status_latest/$', views.work_status_latest),
    url(r'^monit_task/(.+)/$', views.monit_task),
    url(r'^work_task/(.+)/$', views.work_task),
]

urlpatterns = format_suffix_patterns(urlpatterns)

urlpatterns += router.urls
