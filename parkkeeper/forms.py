# coding: utf-8
from django import forms
from parkkeeper import models


class MonitSchedule(forms.ModelForm):

    class Meta:
        model = models.MonitSchedule
        fields = '__all__'
