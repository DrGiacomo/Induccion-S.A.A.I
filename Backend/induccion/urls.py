"""
Rutas del proyecto S.A.A.I.

Las rutas de cada app viven dentro de la app, no aquí. Este archivo reparte
y nada más.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('usuarios.urls')),
    path('api/', include('contenido.urls')),
]

# Servir los archivos subidos durante el desarrollo.
#
# Django hace esto SOLO con DEBUG=True, y es correcto que así sea: este
# servidor es lento y no está pensado para aguantar tráfico. En producción
# los sirve nginx o el bucket. Sin estas dos líneas los documentos se suben
# pero no se pueden abrir, que es exactamente lo que pasaba antes de P0.9.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Los endpoints nacen cerrados: `DEFAULT_PERMISSION_CLASSES` en settings.py
# exige sesión en todo salvo donde se diga lo contrario explícitamente. Solo
# hay dos excepciones, y están declaradas a la vista en `usuarios/urls.py`:
# `auth/csrf/` y `auth/login/`, que no podrían funcionar de otro modo.
