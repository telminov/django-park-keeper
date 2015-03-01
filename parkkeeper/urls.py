# coding: utf-8

from rest_framework import routers
from . import views

router = routers.SimpleRouter()
router.register(r'state', views.StateViewSet)

urlpatterns = [

]

urlpatterns += router.urls
