# ==============================================================================
# Module: fitness_hub.urls
# Description: Root URL configuration
# ==============================================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.views.generic import TemplateView


# ==============================================================================
# SECTION: URL Patterns
# ==============================================================================

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('homepages.urls')),
    path('users/', include('users.urls')),
    path('store/', include('store.urls')),
    path('verify/', include('verification.urls')),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]


# ==============================================================================
# SECTION: Media URLs (Development Only)
# ==============================================================================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ==============================================================================
# SECTION: Error Handlers
# ==============================================================================

def handler404(request, exception=None):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)
