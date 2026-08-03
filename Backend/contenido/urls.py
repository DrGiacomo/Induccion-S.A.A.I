from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CargoViewSet,
    DocumentoViewSet,
    MencionViewSet,
    SinonimoViewSet,
    TerminoViewSet,
)

router = DefaultRouter()
router.register(r"terminos", TerminoViewSet, basename="termino")
router.register(r"sinonimos", SinonimoViewSet, basename="sinonimo")
router.register(r"documentos", DocumentoViewSet, basename="documento")
router.register(r"cargos", CargoViewSet, basename="cargo")
router.register(r"menciones", MencionViewSet, basename="mencion")

urlpatterns = [path("", include(router.urls))]
