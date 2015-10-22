# coding: utf-8

from django import forms

from parkkeeper import models
from parkkeeper.monits.base import Monit

class MonitSchedule(forms.ModelForm):
    monit_name = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['monit_name'].choices = ((name, name)for name, _ in Monit.get_all_monits())

    class Meta:
        model = models.MonitSchedule
        fields = '__all__'