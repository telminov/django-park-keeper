# coding: utf-8
from django.conf.urls import url, patterns
from rest_framework import routers
from parkkeeper import views

router = routers.DefaultRouter()
router.register('host', views.HostViewSet)
router.register('host_group', views.HostGroupViewSet)
router.register('monit_schedule', views.MonitScheduleViewSet)


urlpatterns = patterns('parkkeeper.views',
    url(r'^$', 'index'),
)

urlpatterns += router.urls
