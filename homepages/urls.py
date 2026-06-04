from django.urls import path
from . import views

urlpatterns = [
    # 💡 The root path MUST name the view 'home' so {% url 'home' %} works!
    path('', views.home, name='home'),
]