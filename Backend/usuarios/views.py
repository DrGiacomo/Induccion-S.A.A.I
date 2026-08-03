"""Autenticación y gestión de personal."""

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.middleware.csrf import get_token
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comun.permisos import (
    EsAdmin,
    EsAdminOJefeDeArea,
    Rol,
    area_a_cargo,
    es_admin,
    es_jefe_de_area,
)

from .models import Area, TipoIdentificacion, Usuario, UsuarioArea
from .serializers import (
    AreaSerializer,
    CambiarPasswordSerializer,
    CrearUsuarioSerializer,
    LoginSerializer,
    TipoIdentificacionSerializer,
    UsuarioSerializer,
)


# ══════════════════════════════════════════════════════════════════════
#  Autenticación  (P1.2)
# ══════════════════════════════════════════════════════════════════════

class CsrfView(APIView):
    """
    Entrega la cookie CSRF al frontend antes del login.

    Django protege contra la falsificación de peticiones exigiendo un token
    que el navegador solo obtiene de una cookie. La aplicación de Vue no la
    tiene hasta su primera llamada, así que necesita este endpoint para
    pedirla. Es el único que puede vivir sin sesión, y no entrega nada más.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    """
    Inicia sesión y deja la cookie de sesión en el navegador.

    La cookie es `HttpOnly`: el JavaScript de la página **no puede leerla**.
    Esa es toda la diferencia con guardar un token en `localStorage`, que
    cualquier script inyectado se llevaría de calle.

    `throttle_scope = "login"` limita a 10 intentos por minuto y por IP
    (P1.9). Sin ese tope, probar contraseñas al azar sale gratis: basta
    dejar un script corriendo toda la noche.
    """

    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        usuario = authenticate(
            request,
            username=s.validated_data["username"],
            password=s.validated_data["password"],
        )

        # Mismo mensaje para "no existe" y para "contraseña incorrecta", a
        # propósito. Distinguirlos le confirma a quien prueba al azar qué
        # usuarios existen, que es media faena hecha para él.
        if usuario is None:
            return Response(
                {"detail": "Usuario o contraseña incorrectos."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not usuario.is_active:
            return Response(
                {"detail": "Esta cuenta está desactivada. Habla con tu administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, usuario)
        return Response({
            "usuario": UsuarioSerializer(usuario).data,
            "debe_cambiar_password": usuario.debe_cambiar_password,
            "es_admin": es_admin(usuario),
            "es_jefe_de_area": es_jefe_de_area(usuario),
        })


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"detail": "Sesión cerrada."})


class YoView(APIView):
    """Quién soy. El frontend lo llama al arrancar para saber si hay sesión."""

    def get(self, request):
        return Response({
            "usuario": UsuarioSerializer(request.user).data,
            "debe_cambiar_password": request.user.debe_cambiar_password,
            "es_admin": es_admin(request.user),
            "es_jefe_de_area": es_jefe_de_area(request.user),
        })


class CambiarPasswordView(APIView):
    """
    Cambio de contraseña. Obligatorio en el primer ingreso.

    Las credenciales se entregan en mano, así que hasta que se cambien hay
    otra persona que las conoce. `debe_cambiar_password` se apaga aquí y en
    ningún otro sitio.
    """

    def post(self, request):
        s = CambiarPasswordSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)

        usuario = request.user
        usuario.set_password(s.validated_data["password_nueva"])
        usuario.debe_cambiar_password = False
        usuario.save(update_fields=["password", "debe_cambiar_password"])

        # Cambiar la contraseña invalida la sesión actual. Se vuelve a
        # iniciar para que el usuario no salga expulsado de su propia
        # pantalla justo después de hacer lo que le pedimos.
        login(request, usuario)
        return Response({"detail": "Contraseña actualizada."})


# ══════════════════════════════════════════════════════════════════════
#  Gestión de personal  (P1.5)
# ══════════════════════════════════════════════════════════════════════

class UsuarioViewSet(viewsets.ModelViewSet):
    permission_classes = [EsAdminOJefeDeArea]
    search_fields = ["username", "first_name", "last_name", "numero_identificacion", "email"]
    ordering_fields = ["first_name", "last_name", "username", "date_joined"]

    def get_serializer_class(self):
        return CrearUsuarioSerializer if self.action == "create" else UsuarioSerializer

    def get_queryset(self):
        """
        Un jefe de área solo ve —y por tanto solo puede tocar— a la gente de
        su área.

        El filtro va en el queryset y no en una comprobación aparte: así vale
        igual para listar, para pedir el detalle por id y para editar, sin
        que haya que acordarse de repetirlo en cada método. Es donde no se
        escapan las fugas.
        """
        base = (
            Usuario.objects.select_related("tipo_identificacion", "cargo", "area_a_cargo")
            .prefetch_related("groups", "areas_asignadas__area")
        )
        if es_admin(self.request.user):
            return base
        propia = area_a_cargo(self.request.user)
        if not propia:
            return base.none()
        return base.filter(areas_asignadas__area=propia).distinct()

    def perform_destroy(self, instance):
        """
        Nunca se borra un usuario: se desactiva (P7).

        Pero **sí se borra su historial personal de consultas**, y no es una
        contradicción: P7 protege el *contenido de la empresa*, no los datos
        personales de alguien que ya no trabaja aquí. La Ley 1581 de 2012
        dice que los datos personales se conservan mientras haya una
        finalidad, y un extrabajador ya no la tiene.

        Los contadores anónimos **sobreviven**. Si se borrara todo, cada
        salida se llevaría un pedazo de las estadísticas y el dashboard de la
        Fase 5 acabaría mintiendo.
        """
        with transaction.atomic():
            borradas = instance.consultas.all().delete()[0]
            instance.is_active = False
            instance.save(update_fields=["is_active"])
        self._consultas_borradas = borradas

    def destroy(self, request, *args, **kwargs):
        instancia = self.get_object()
        if instancia == request.user:
            return Response(
                {"detail": "No puedes desactivar tu propia cuenta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instancia)
        return Response({
            "detail": f"«{instancia}» quedó desactivado.",
            "consultas_borradas": getattr(self, "_consultas_borradas", 0),
        })

    @action(detail=True, methods=["post"], permission_classes=[EsAdmin])
    def reactivar(self, request, pk=None):
        usuario = self.get_object()
        usuario.is_active = True
        usuario.save(update_fields=["is_active"])
        return Response({"detail": f"«{usuario}» reactivado."})

    @action(detail=True, methods=["post"])
    def resetear_password(self, request, pk=None):
        """La pone quien resetea, y el usuario está obligado a cambiarla."""
        usuario = self.get_object()
        nueva = request.data.get("password_nueva", "")
        if len(nueva) < 8:
            return Response(
                {"password_nueva": "Mínimo 8 caracteres."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.set_password(nueva)
        usuario.debe_cambiar_password = True
        usuario.save(update_fields=["password", "debe_cambiar_password"])
        return Response({"detail": f"Contraseña de «{usuario}» reiniciada. Debe cambiarla al entrar."})


class AreaViewSet(viewsets.ModelViewSet):
    """
    Las áreas las administra el administrador; los demás solo las consultan.
    Saber qué áreas existen no es información sensible, y el sidebar la
    necesita para funcionar.
    """

    queryset = Area.objects.select_related("jefe").all()
    serializer_class = AreaSerializer
    search_fields = ["nombre", "descripcion"]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EsAdmin()]

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user, actualizado_por=self.request.user)

    def perform_update(self, serializer):
        serializer.save(actualizado_por=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[EsAdmin])
    def nombrar_jefe(self, request, pk=None):
        """
        Solo el administrador nombra jefes de área.

        `permission_classes=[EsAdmin]` en la acción es lo que impide que un
        jefe se ascienda a sí mismo llamando a la API a mano. Ocultar el
        botón en la interfaz no habría servido de nada: la interfaz no es una
        barrera de seguridad.
        """
        from django.contrib.auth.models import Group

        area = self.get_object()
        usuario = Usuario.objects.filter(pk=request.data.get("usuario_id"), is_active=True).first()
        if not usuario:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        otra = getattr(usuario, "area_a_cargo", None)
        if otra and otra.id != area.id:
            return Response(
                {"detail": f"«{usuario}» ya dirige «{otra.nombre}». Un jefe responde por una sola área."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        area.jefe = usuario
        area.actualizado_por = request.user
        area.save(update_fields=["jefe", "actualizado_por", "actualizado_en"])

        grupo = Group.objects.filter(name=Rol.JEFE_AREA).first()
        if grupo:
            usuario.groups.add(grupo)
        usuario.is_staff = True
        usuario.save(update_fields=["is_staff"])
        UsuarioArea.objects.get_or_create(
            usuario=usuario, area=area, defaults={"creado_por": request.user}
        )
        return Response({"detail": f"«{usuario}» ahora dirige «{area.nombre}»."})


class TipoIdentificacionViewSet(viewsets.ModelViewSet):
    queryset = TipoIdentificacion.objects.all()
    serializer_class = TipoIdentificacionSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EsAdmin()]
