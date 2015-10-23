# coding: utf-8
from django.conf.urls import url, patterns

urlpatterns = patterns('parkkeeper.views',
    url(r'^$', 'index'),
)