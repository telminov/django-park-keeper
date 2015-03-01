# coding: utf-8
from django.conf.urls import url
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r'state', views.StateViewSet)

urlpatterns = [
    url('^state/(?P<state_id>\d+)/results/$', views.CheckResults.as_view()),
]

urlpatterns += router.urls
