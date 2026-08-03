"""
Backoffice del rastro  (P1.6).

Lo único que se administra aquí es `BusquedaSinResultado`, y merece la pena
explicar por qué: **cada fila es un hueco concreto en la biblioteca**,
escrito por alguien que lo necesitaba de verdad.

Es la lista de tareas del jefe de área, redactada por sus propios compañeros
sin que nadie se lo pidiera.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import BusquedaSinResultado, Consulta, ContadorTermino


@admin.register(BusquedaSinResultado)
class BusquedaSinResultadoAdmin(admin.ModelAdmin):
    list_display = ["texto", "veces_destacado", "resuelto", "primera_vez", "ultima_vez"]
    list_filter = ["resuelto"]
    search_fields = ["texto"]
    readonly_fields = ["texto", "veces", "primera_vez", "ultima_vez"]
    actions = ["marcar_resuelto"]

    @admin.display(description="Veces", ordering="veces")
    def veces_destacado(self, obj):
        if obj.veces >= 10:
            return format_html('<b style="color:#c00">{} ×</b>', obj.veces)
        if obj.veces >= 3:
            return format_html('<b style="color:#c60">{} ×</b>', obj.veces)
        return f"{obj.veces} ×"

    @admin.action(description="Marcar como documentado")
    def marcar_resuelto(self, request, queryset):
        n = queryset.update(resuelto=True)
        self.message_user(request, f"{n} búsqueda(s) marcadas como documentadas.")

    def has_add_permission(self, request):
        return False        # las escribe el buscador, no una persona


@admin.register(ContadorTermino)
class ContadorTerminoAdmin(admin.ModelAdmin):
    list_display = ["termino", "veces_consultado", "ultima_consulta"]
    search_fields = ["termino__nombre"]
    readonly_fields = ["termino", "veces_consultado", "ultima_consulta"]

    def has_add_permission(self, request):
        return False


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    """
    El historial personal. Solo lectura y solo para administradores.

    Son datos personales: quién buscó qué y cuándo. Se muestran para poder
    depurar, no para vigilar a nadie. Se borran solos al desactivar al
    usuario (Ley 1581 de 2012).
    """

    list_display = ["usuario", "texto", "num_resultados", "creado_en"]
    list_filter = ["creado_en"]
    search_fields = ["texto", "usuario__username"]
    readonly_fields = ["usuario", "texto", "num_resultados", "creado_en"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
