from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from homepages import views as homepage_views

urlpatterns = [
    path('', homepage_views.home, name='home'),
    # Set homepages app as the root URL
   path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('store/', include('store.urls')),
    path('inspiration/', include('inspiration.urls')),
    # ADD THIS LINE:
    path('exercises/', include('exercises.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)