from django.urls import path
from . import views

urlpatterns = [
    path('setup/', views.verification_setup, name='verification_setup'),
    path('email/send/', views.send_email_verification, name='send_email_verification'),
    path('email/verify/', views.verify_email_otp, name='verify_email_otp'),
    path('email/verify/<str:token>/', views.verify_email_token, name='verify_email_token'),
    path('email/resend/', views.resend_email_verification, name='resend_email_verification'),

    path('phone/send/', views.send_phone_verification, name='send_phone_verification'),
    path('phone/verify/', views.verify_phone_otp, name='verify_phone_otp'),
    path('phone/resend/', views.resend_phone_verification, name='resend_phone_verification'),
]
