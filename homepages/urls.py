from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index_home'), # Use a distinct name like 'index_home' to avoid clashes!
]