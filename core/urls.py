from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('marketplace.urls')),
]

# ── Serve uploaded media files in development ──────────────────────────────
# In production, your web server (Nginx/Apache) or a CDN should serve /media/.
# Django's dev server does NOT serve media by default without this block.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)