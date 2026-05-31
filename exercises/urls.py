
# exercises/urls.py
from django.urls import path
from . import views  # The dot means "from the current folder"

urlpatterns = [
    path('', views.index, name='exercises-index'), 
]