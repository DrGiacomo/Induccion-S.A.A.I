"""
Rutas del proyecto S.A.A.I.

Las rutas de cada app viven dentro de la app, no aquí. Este archivo reparte
y nada más.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Servir los archivos subidos durante el desarrollo.
#
# Django hace esto SOLO con DEBUG=True, y es correcto que así sea: este
# servidor es lento y no está pensado para aguantar tráfico. En producción
# los sirve nginx o el bucket. Sin estas dos líneas los documentos se suben
# pero no se pueden abrir, que es exactamente lo que pasaba antes de P0.9.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Las rutas de la API llegan en la Fase 1, cuando exista con qué protegerlas.
# Publicar endpoints antes de tener permisos es justo lo que dejó la API
# abierta de par en par la primera vez.
