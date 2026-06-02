from django.urls import path
from . import views

urlpatterns = [
    # 💡 FIX: Removed the duplicate path('', views.home, name='home') line!
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
]