"""Root URL configuration."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap


sitemaps = {
    'static': StaticViewSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('homepages.urls')),
    path('users/', include('users.urls')),
    path('store/', include('store.urls')),
    path('verify/', include('verification.urls')),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('google303d3f39c4a640fc.html', lambda r: HttpResponse('google-site-verification: google303d3f39c4a640fc.html', content_type='text/plain')),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



def handler404(request, exception=None):
    return render(request, '404.html', status=404)

def handler500(request):
    return HttpResponse("""
<!DOCTYPE html><html><head><title>Server Error — FITNESS HUB</title>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>body{background:#0d0d0d;color:#f0ece4;font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center;padding:2rem}
h1{font-size:5rem;font-weight:800;color:#d4af37;margin:0 0 0.5rem;line-height:1}
p{color:#888;max-width:400px;margin:0 0 2rem}
a{display:inline-flex;align-items:center;gap:8px;background:#d4af37;color:#0d0d0d;padding:12px 28px;border-radius:50px;font-weight:700;text-decoration:none}
</style></head><body><div><h1>500</h1><p>Something went wrong. Please try again in a moment.</p><a href="/">← Back to Home</a></div></body></html>
""", status=500)
