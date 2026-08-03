"""
Endpoints del contenido.

Todos los `get_queryset` de este archivo llaman a `visibles_para(usuario)`.
**Uno que se olvide es una fuga**, y las fugas de permisos no avisan: el
endpoint funciona perfectamente, solo que para la persona equivocada. Por eso
`P2.7` monta una suite que debe fallar si alguien quita ese filtro.
"""

from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from comun.modelos import EstadoContenido
from comun.permisos import (
    LecturaParaTodosEscrituraParaCuradores,
    area_a_cargo,
    es_admin,
)

from .models import Cargo, Documento, MencionEnDocumento, Sinonimo, Termino
from .serializers import (
    CargoSerializer,
    DocumentoSerializer,
    MencionSerializer,
    SinonimoSerializer,
    TerminoListaSerializer,
    TerminoSerializer,
)


class BaseContenidoViewSet(viewsets.ModelViewSet):
    """
    Lo común a todo el contenido: el filtro de visibilidad y la autoría.

    Se hereda en vez de repetirse justamente para que no se pueda olvidar.
    """

    permission_classes = [LecturaParaTodosEscrituraParaCuradores]

    def get_queryset(self):
        return self.queryset.visibles_para(self.request.user)

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user, actualizado_por=self.request.user)

    def perform_update(self, serializer):
        serializer.save(actualizado_por=self.request.user)

    def perform_destroy(self, instancia):
        """
        Nada se borra: se archiva (P7).

        Un `DELETE` sobre contenido no lo hace desaparecer — lo marca como
        archivado, con fecha y autor. Si desapareciera, un procedimiento
        podría citar un término que ya no existe y nadie sabría por qué.
        """
        instancia.estado = EstadoContenido.ARCHIVADO
        instancia.actualizado_por = self.request.user
        instancia.save(update_fields=["estado", "actualizado_por", "actualizado_en"])

    def destroy(self, request, *args, **kwargs):
        instancia = self.get_object()
        self.perform_destroy(instancia)
        return Response(
            {"detail": f"«{instancia}» quedó archivado. No se borró: se puede recuperar."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def publicar(self, request, pk=None):
        """
        Saca el contenido del borrador. **Este es el punto donde se cumple P1.**

        Todo lo que proponga la ingesta automática en la Fase 4 va a pasar por
        aquí, y solo por aquí. Si algún día aparece otra ruta que ponga algo
        en estado publicado sin un humano detrás, eso es un bug, no una
        funcionalidad.
        """
        obj = self.get_object()
        if not self._puede_curar(obj):
            return Response(
                {"detail": "Solo el jefe de esa área o un administrador puede publicar."},
                status=status.HTTP_403_FORBIDDEN,
            )
        obj.estado = EstadoContenido.PUBLICADO
        obj.actualizado_por = request.user
        obj.save(update_fields=["estado", "actualizado_por", "actualizado_en"])
        return Response({"detail": f"«{obj}» publicado.", "estado": obj.estado})

    @action(detail=True, methods=["post"])
    def devolver_a_borrador(self, request, pk=None):
        obj = self.get_object()
        if not self._puede_curar(obj):
            return Response({"detail": "No tienes permiso."}, status=status.HTTP_403_FORBIDDEN)
        obj.estado = EstadoContenido.BORRADOR
        obj.actualizado_por = request.user
        obj.save(update_fields=["estado", "actualizado_por", "actualizado_en"])
        return Response({"detail": f"«{obj}» devuelto a borrador.", "estado": obj.estado})

    def _puede_curar(self, obj) -> bool:
        if es_admin(self.request.user):
            return True
        propia = area_a_cargo(self.request.user)
        if not propia:
            return False
        areas = getattr(obj, "areas", None)
        if areas is None:
            return getattr(obj, "area_id", None) == propia.id
        return propia.id in set(areas.values_list("id", flat=True))


class TerminoViewSet(BaseContenidoViewSet):
    queryset = Termino.objects.prefetch_related(
        "areas", "sinonimos", Prefetch("menciones", queryset=MencionEnDocumento.objects.select_related("documento"))
    ).select_related("creado_por")
    search_fields = ["nombre", "definicion", "sinonimos__texto"]
    ordering_fields = ["nombre", "creado_en"]

    def get_serializer_class(self):
        return TerminoListaSerializer if self.action == "list" else TerminoSerializer

    @action(detail=False, methods=["get"])
    def borradores(self, request):
        """
        La bandeja de curaduría del jefe de área: lo que espera aprobación.

        En la Fase 4 esta pantalla se llena sola con lo que proponga la IA.
        Hoy solo muestra lo que alguien dejó a medias, pero se construye ya
        porque es la que hace posible que P1 se cumpla sin fricción.
        """
        qs = self.get_queryset().filter(estado=EstadoContenido.BORRADOR)
        pagina = self.paginate_queryset(qs)
        s = TerminoListaSerializer(pagina, many=True, context={"request": request})
        return self.get_paginated_response(s.data)


class SinonimoViewSet(viewsets.ModelViewSet):
    permission_classes = [LecturaParaTodosEscrituraParaCuradores]
    serializer_class = SinonimoSerializer

    def get_queryset(self):
        # Un sinónimo hereda la visibilidad de su término: si el término no
        # se puede ver, sus sinónimos tampoco.
        visibles = Termino.objects.visibles_para(self.request.user)
        return Sinonimo.objects.filter(termino__in=visibles).select_related("termino")

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user, actualizado_por=self.request.user)


class DocumentoViewSet(BaseContenidoViewSet):
    queryset = Documento.objects.prefetch_related("areas").select_related("creado_por")
    serializer_class = DocumentoSerializer
    search_fields = ["nombre", "descripcion", "texto_extraido"]
    ordering_fields = ["nombre", "creado_en"]

    @action(detail=True, methods=["post"])
    def reemplazar(self, request, pk=None):
        """
        Sustituye el archivo dejando el anterior archivado y recuperable.

        No es versionado tipo SharePoint —eso está en el §2— es un "deshacer".
        """
        viejo = self.get_object()
        if not self._puede_curar(viejo):
            return Response({"detail": "No tienes permiso."}, status=status.HTTP_403_FORBIDDEN)

        s = DocumentoSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        nuevo = s.save(creado_por=request.user, actualizado_por=request.user,
                       estado=viejo.estado)
        nuevo.areas.set(viejo.areas.all())
        viejo.archivar_y_reemplazar(nuevo, usuario=request.user)
        return Response(
            {"detail": f"Reemplazado. La versión anterior quedó archivada.",
             "nuevo_id": nuevo.id, "anterior_id": viejo.id},
            status=status.HTTP_201_CREATED,
        )


class CargoViewSet(BaseContenidoViewSet):
    queryset = Cargo.objects.select_related("area", "reporta_a").prefetch_related("terminos", "documentos")
    serializer_class = CargoSerializer
    search_fields = ["nombre", "descripcion", "funciones"]
    ordering_fields = ["nombre"]

    @action(detail=False, methods=["get"])
    def mi_induccion(self, request):
        """
        Lo que esta persona debería leer, según su cargo.

        **Aquí es donde la inducción emerge sin que exista un LMS.** No hay
        rutas formativas ni módulos ni secuencias: hay un cargo con contenido
        enganchado y una persona con ese cargo. El sistema deduce el resto.
        """
        cargo = getattr(request.user, "cargo", None)
        if not cargo:
            return Response({
                "cargo": None,
                "mensaje": "Todavía no tienes un cargo asignado. Pídeselo a tu jefe de área.",
                "terminos": [], "documentos": [],
            })

        visibles_t = Termino.objects.visibles_para(request.user)
        visibles_d = Documento.objects.visibles_para(request.user)
        return Response({
            "cargo": CargoSerializer(cargo, context={"request": request}).data,
            "terminos": TerminoListaSerializer(
                cargo.terminos.filter(pk__in=visibles_t), many=True, context={"request": request}
            ).data,
            "documentos": DocumentoSerializer(
                cargo.documentos.filter(pk__in=visibles_d), many=True, context={"request": request}
            ).data,
        })


class MencionViewSet(viewsets.ModelViewSet):
    permission_classes = [LecturaParaTodosEscrituraParaCuradores]
    serializer_class = MencionSerializer

    def get_queryset(self):
        visibles = Termino.objects.visibles_para(self.request.user)
        return MencionEnDocumento.objects.filter(termino__in=visibles).select_related("documento", "termino")

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user, actualizado_por=self.request.user)
