from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('gestion-kairos-secure-security-not-for-all-666/', admin.site.urls),
    path('', include('appKairos.urls')),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    # Servir archivos estáticos desde STATICFILES_DIRS
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    # Servir archivos media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Personalización del admin
admin.site.site_header = "Proyecto Kairos Admin"
admin.site.site_title = "Kairos Admin Portal"
admin.site.index_title = "Welcome to Proyecto Kairos Administration"