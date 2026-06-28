"""User URL routing."""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-reset/',
         views.CustomPasswordResetView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         views.CustomPasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]