"""URL patterns for homepage and static pages."""

from django.urls import path
from . import views

# ==============================================================================
# SECTION: URL Patterns
# ==============================================================================

urlpatterns = [
    # 💡 The root path MUST name the view 'home' so {% url 'home' %} works!
    path('', views.home, name='home'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', views.TermsOfServiceView.as_view(), name='terms'),
    path('cookies/', views.CookiesPolicyView.as_view(), name='cookies'),
]