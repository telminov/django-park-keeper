# coding: utf-8
import rest_framework.serializers
from parkkeeper import models


class Host(rest_framework.serializers.ModelSerializer):
    class Meta:
        model = models.Host
