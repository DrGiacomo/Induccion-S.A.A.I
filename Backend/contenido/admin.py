"""
Backoffice del contenido  (P1.6).

Es la primera pantalla de curaduría que existe. Las de Vue llegan en `P2.4`,
pero mientras tanto un jefe de área ya puede cargar términos y documentos
desde aquí, con buscador, filtros y validación — sin escribir una vista.

El filtro por área se aplica también en el panel: un jefe solo ve lo suyo.
Es fácil de olvidar y es un hueco del mismo tamaño que dejar la API abierta.
"""

from django.contrib import admin
from django.utils.html import format_html

from comun.modelos import EstadoContenido
from comun.permisos import area_a_cargo, es_admin

from .models import Cargo, Documento, MencionEnDocumento, Sinonimo, Termino


class FiltradoPorAreaMixin:
    """El jefe de área ve lo suyo; el administrador, todo."""

    campo_area = "areas"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if es_admin(request.user):
            return qs
        propia = area_a_cargo(request.user)
        if not propia:
            return qs.none()
        filtro = {self.campo_area: propia}
        return qs.filter(**filtro).distinct()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)


class SinonimoInline(admin.TabularInline):
    model = Sinonimo
    extra = 2
    fields = ["texto"]
    verbose_name_plural = 'Sinónimos — "la 47", "merma de turno"…  Ninguna tecnología los adivina'


class MencionInline(admin.TabularInline):
    model = MencionEnDocumento
    extra = 1
    autocomplete_fields = ["documento"]
    fields = ["documento", "ubicacion", "fragmento"]
    verbose_name_plural = "Dónde aparece — el fragmento se copia literal, no se parafrasea (P6)"


@admin.register(Termino)
class TerminoAdmin(FiltradoPorAreaMixin, admin.ModelAdmin):
    inlines = [SinonimoInline, MencionInline]
    list_display = ["nombre", "areas_texto", "publica", "estado_color", "sinonimos_n", "actualizado_en"]
    list_filter = ["estado", "definicion_es_publica", "areas"]
    search_fields = ["nombre", "definicion", "detalle", "sinonimos__texto"]
    filter_horizontal = ["areas"]
    readonly_fields = ["creado_en", "actualizado_en", "creado_por", "actualizado_por"]
    actions = ["publicar", "devolver_a_borrador", "archivar"]

    fieldsets = (
        (None, {"fields": ("nombre", "estado")}),
        ("Capa pública — la ve toda la empresa", {
            "fields": ("definicion", "definicion_es_publica"),
            "description": (
                "Una o dos frases. Si desmarcas «pública», el término desaparece "
                "por completo para el resto de la empresa: ni se sabrá que existe. "
                "Úsalo solo cuando el concepto en sí sea sensible."
            ),
        }),
        ("Capa restringida — solo las áreas dueñas", {
            "fields": ("detalle", "ejemplo"),
            "description": "Cómo se calcula, con qué formato, en qué procedimiento aparece.",
        }),
        ("Propiedad", {
            "fields": ("areas",),
            "description": "Vacío = transversal, lo ve toda la empresa. Varias áreas = definición compartida.",
        }),
        ("Auditoría", {"fields": ("creado_en", "creado_por", "actualizado_en", "actualizado_por"),
                       "classes": ("collapse",)}),
    )

    @admin.display(description="Áreas")
    def areas_texto(self, obj):
        nombres = [a.nombre for a in obj.areas.all()]
        return ", ".join(nombres) if nombres else format_html('<em style="color:#0a0">transversal</em>')

    @admin.display(description="Def. pública", boolean=True)
    def publica(self, obj):
        return obj.definicion_es_publica

    @admin.display(description="Estado")
    def estado_color(self, obj):
        colores = {"borrador": "#c60", "publicado": "#0a0", "archivado": "#999"}
        return format_html(
            '<b style="color:{}">{}</b>', colores.get(obj.estado, "#000"), obj.get_estado_display()
        )

    @admin.display(description="Sinón.")
    def sinonimos_n(self, obj):
        return obj.sinonimos.count()

    @admin.action(description="Publicar — visible para quien corresponda")
    def publicar(self, request, queryset):
        n = queryset.update(estado=EstadoContenido.PUBLICADO, actualizado_por=request.user)
        self.message_user(request, f"{n} término(s) publicados.")

    @admin.action(description="Devolver a borrador")
    def devolver_a_borrador(self, request, queryset):
        n = queryset.update(estado=EstadoContenido.BORRADOR, actualizado_por=request.user)
        self.message_user(request, f"{n} término(s) devueltos a borrador.")

    @admin.action(description="Archivar — no se borra, se puede recuperar (P7)")
    def archivar(self, request, queryset):
        n = queryset.update(estado=EstadoContenido.ARCHIVADO, actualizado_por=request.user)
        self.message_user(request, f"{n} término(s) archivados.")


@admin.register(Documento)
class DocumentoAdmin(FiltradoPorAreaMixin, admin.ModelAdmin):
    list_display = ["nombre", "areas_texto", "estado", "tamano", "ocr", "creado_en"]
    list_filter = ["estado", "texto_por_ocr", "areas"]
    search_fields = ["nombre", "descripcion", "texto_extraido"]
    filter_horizontal = ["areas"]
    readonly_fields = ["tipo_mime", "tamano_bytes", "creado_en", "actualizado_en",
                       "creado_por", "actualizado_por"]
    actions = ["publicar", "archivar"]

    fieldsets = (
        (None, {"fields": ("nombre", "descripcion", "estado")}),
        ("El archivo", {
            "fields": ("archivo", "enlace_externo", "tipo_mime", "tamano_bytes"),
            "description": (
                "Máximo 50 MB. El video NO se sube: se enlaza — alojar y transmitir "
                "video es otro proyecto, y un video no es buscable de todos modos."
            ),
        }),
        ("Propiedad", {"fields": ("areas",),
                       "description": "Vacío = transversal."}),
        ("Texto extraído", {
            "fields": ("texto_extraido", "texto_por_ocr", "reemplaza_a"),
            "classes": ("collapse",),
            "description": "Se llena solo en la Fase 4. El original siempre manda sobre esto (P6).",
        }),
        ("Auditoría", {"fields": ("creado_en", "creado_por", "actualizado_en", "actualizado_por"),
                       "classes": ("collapse",)}),
    )

    @admin.display(description="Áreas")
    def areas_texto(self, obj):
        nombres = [a.nombre for a in obj.areas.all()]
        return ", ".join(nombres) if nombres else format_html('<em style="color:#0a0">transversal</em>')

    @admin.display(description="Tamaño")
    def tamano(self, obj):
        n = obj.tamano_bytes or 0
        for u in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.0f} {u}"
            n /= 1024
        return f"{n:.1f} TB"

    @admin.display(description="OCR", boolean=True)
    def ocr(self, obj):
        return obj.texto_por_ocr

    def save_model(self, request, obj, form, change):
        if obj.archivo:
            obj.tamano_bytes = obj.archivo.size
        super().save_model(request, obj, form, change)

    @admin.action(description="Publicar")
    def publicar(self, request, queryset):
        n = queryset.update(estado=EstadoContenido.PUBLICADO, actualizado_por=request.user)
        self.message_user(request, f"{n} documento(s) publicados.")

    @admin.action(description="Archivar — no se borra (P7)")
    def archivar(self, request, queryset):
        n = queryset.update(estado=EstadoContenido.ARCHIVADO, actualizado_por=request.user)
        self.message_user(request, f"{n} documento(s) archivados.")


@admin.register(Cargo)
class CargoAdmin(FiltradoPorAreaMixin, admin.ModelAdmin):
    campo_area = "area"           # el cargo pertenece a UN área, no a varias
    list_display = ["nombre", "area", "personas_n", "terminos_n", "documentos_n", "estado"]
    list_filter = ["estado", "area"]
    search_fields = ["nombre", "descripcion", "funciones"]
    filter_horizontal = ["terminos", "documentos"]
    autocomplete_fields = ["area", "reporta_a"]
    readonly_fields = ["creado_en", "actualizado_en", "creado_por", "actualizado_por"]

    fieldsets = (
        (None, {"fields": ("nombre", "area", "reporta_a", "estado")}),
        ("Qué hace", {"fields": ("descripcion", "funciones")}),
        ("Su inducción", {
            "fields": ("terminos", "documentos"),
            "description": (
                "Lo que engancnes aquí es lo que verá en su pantalla de inicio quien "
                "tenga este cargo, el día que entre. La ruta de inducción no se "
                "programa: sale de aquí."
            ),
        }),
        ("Auditoría", {"fields": ("creado_en", "creado_por", "actualizado_en", "actualizado_por"),
                       "classes": ("collapse",)}),
    )

    @admin.display(description="Personas")
    def personas_n(self, obj):
        return obj.personas.count()

    @admin.display(description="Términos")
    def terminos_n(self, obj):
        return obj.terminos.count()

    @admin.display(description="Docs")
    def documentos_n(self, obj):
        return obj.documentos.count()


@admin.register(Sinonimo)
class SinonimoAdmin(admin.ModelAdmin):
    list_display = ["texto", "termino"]
    search_fields = ["texto", "termino__nombre"]
    autocomplete_fields = ["termino"]


@admin.register(MencionEnDocumento)
class MencionAdmin(admin.ModelAdmin):
    list_display = ["termino", "documento", "ubicacion"]
    search_fields = ["termino__nombre", "documento__nombre", "fragmento"]
    autocomplete_fields = ["termino", "documento"]
