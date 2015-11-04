# coding: utf-8
import json

from django import forms
from parkkeeper import models


class MonitSchedule(forms.ModelForm):

    class Meta:
        model = models.MonitSchedule
        fields = '__all__'

    def clean_options_json(self):
        options_json = self.cleaned_data.get('options_json')

        if options_json:
            try:
                options = json.loads(options_json)
            except ValueError:
                raise forms.ValidationError('Incorrect JSON')

            if type(options) is not dict:
                raise forms.ValidationError('Options must be JavaScript object.')

        return options_json

    def clean(self):
        all_hosts = set(self.cleaned_data['hosts'].all())
        for group in self.cleaned_data['groups'].all():
            all_hosts.update(group.hosts.all())

        not_exists_host_credentials = set()
        for credential_type in self.cleaned_data['credential_types'].all():
            for host in all_hosts:
                qs = models.HostCredential.objects.filter(host=host, credential__type=credential_type)
                if not qs.exists():
                    not_exists_host_credentials.add((host, credential_type))
        if not_exists_host_credentials:
            msg = 'Needs credential types for hosts: '
            msg += '. '.join(map(lambda h_ct_args: '%s - %s' % h_ct_args, not_exists_host_credentials))
            self.add_error('hosts', msg)
            self.add_error('groups', msg)
            self.add_error('credential_types', msg)


class Credential(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = models.Credential
        fields = ('name', 'type', 'username', )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            self.instance.set_password(password, save=False)
        elif not self.instance.id:
            raise forms.ValidationError('Password is required for new credential instance.')
        return password
