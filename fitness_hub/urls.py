from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('users.urls')),          # Home and User related
    # path('exercises/', include('exercises.urls')),
    # path('store/', include('store.urls')),
    # path('inspiration/', include('inspiration.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)