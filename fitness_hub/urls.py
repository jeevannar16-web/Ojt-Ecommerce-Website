from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 💡 FIX: Route the root domain through lude('homepagthe homepages app URLs file
   
    
    path('admin/', admin.site.urls),
    
    path('', include('homepages.urls')),
    path('users/', include('users.urls')),
  
    path('inspiration/', include('inspiration.urls')),
    path('exercises/', include('exercises.urls')),
     path('store/', include('store.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)