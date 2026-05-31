from django.shortcuts import render

# Create your views here.
# exercises/views.py
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello! This is the exercises page.")