# coding: utf-8

from . import models
from django.shortcuts import render


def index(request):
    return render(request, 'index.html')
