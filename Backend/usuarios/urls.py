from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AreaViewSet,
    CambiarPasswordView,
    CsrfView,
    LoginView,
    LogoutView,
    TipoIdentificacionViewSet,
    UsuarioViewSet,
    YoView,
)

router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuario")
router.register(r"areas", AreaViewSet, basename="area")
router.register(r"tipos-identificacion", TipoIdentificacionViewSet, basename="tipo-identificacion")

urlpatterns = [
    # Autenticación. `csrf` y `login` son los dos únicos que no exigen sesión
    # —no podrían—; el resto hereda `IsAuthenticated` de la configuración
    # global, que es lo que hace que nada nazca abierto por descuido.
    path("auth/csrf/", CsrfView.as_view(), name="csrf"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/yo/", YoView.as_view(), name="yo"),
    path("auth/cambiar-password/", CambiarPasswordView.as_view(), name="cambiar-password"),

    path("", include(router.urls)),
]
