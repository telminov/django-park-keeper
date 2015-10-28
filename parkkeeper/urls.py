# coding: utf-8
from django.conf.urls import url, patterns
from rest_framework import routers
from parkkeeper import views

router = routers.DefaultRouter()
router.register('host', views.HostViewSet)


urlpatterns = patterns('parkkeeper.views',
    url(r'^$', 'index'),
)

urlpatterns += router.urls
