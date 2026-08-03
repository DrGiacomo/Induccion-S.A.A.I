"""
Backoffice de identidad  (P1.6).

Django trae un panel de administración completo y probado: listados con
paginación, buscador, filtros, formularios con validación, historial de
cambios y permisos por modelo. Configurarlo cuesta unas líneas por modelo.

**Eso significa que buena parte de los CRUD que faltaban no hay que
construirlos.** El esfuerzo de Vue se reserva para el buscador y para lo que
ve el trabajador, que es donde el proyecto se juega su valor (P5, P8).

⚠️ Regla que no se rompe: al trabajador raso **nunca** se le da `is_staff`.
El panel es para administradores y jefes de área.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdminBase
from django.utils.html import format_html

from comun.permisos import area_a_cargo, es_admin

from .models import Area, TipoIdentificacion, Usuario, UsuarioArea


class UsuarioAreaInline(admin.TabularInline):
    model = UsuarioArea
    fk_name = "usuario"
    extra = 1
    autocomplete_fields = ["area"]
    verbose_name = "Área asignada"
    verbose_name_plural = "Áreas asignadas"


@admin.register(Usuario)
class UsuarioAdmin(UserAdminBase):
    inlines = [UsuarioAreaInline]
    list_display = ["username", "nombre", "identificacion", "cargo", "areas_texto", "roles", "is_active"]
    list_filter = ["is_active", "is_staff", "groups", "debe_cambiar_password", "areas_asignadas__area"]
    search_fields = ["username", "first_name", "last_name", "email", "numero_identificacion"]
    ordering = ["first_name", "last_name"]
    autocomplete_fields = ["cargo", "tipo_identificacion"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos personales", {
            "fields": ("first_name", "last_name", "email",
                       "tipo_identificacion", "numero_identificacion", "telefono"),
        }),
        ("En la empresa", {"fields": ("cargo",)}),
        ("Acceso", {
            "fields": ("is_active", "debe_cambiar_password", "is_staff", "is_superuser", "groups"),
            "description": (
                "«Debe cambiar la contraseña» se marca solo al crear el usuario: "
                "quien entregó las credenciales también las conoce. "
                "«Es staff» da acceso a este panel — no se lo des a un trabajador raso."
            ),
        }),
        ("Fechas", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "first_name", "last_name", "email",
                       "tipo_identificacion", "numero_identificacion", "telefono",
                       "password1", "password2", "groups"),
        }),
    )

    @admin.display(description="Nombre")
    def nombre(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="Identificación")
    def identificacion(self, obj):
        return obj.identificacion or "—"

    @admin.display(description="Áreas")
    def areas_texto(self, obj):
        nombres = [ua.area.nombre for ua in obj.areas_asignadas.all()]
        return ", ".join(nombres) if nombres else "—"

    @admin.display(description="Roles")
    def roles(self, obj):
        return ", ".join(obj.groups.values_list("name", flat=True)) or "—"

    def get_queryset(self, request):
        """
        **El filtro por área también rige aquí.** Un jefe de área solo ve a
        la gente de su área en el panel.

        Es fácil de olvidar: se protege la API con esmero y se deja el panel
        abierto, cuando el panel es una API más — solo que con formularios.
        """
        qs = super().get_queryset(request).prefetch_related("groups", "areas_asignadas__area")
        if es_admin(request.user):
            return qs
        propia = area_a_cargo(request.user)
        return qs.filter(areas_asignadas__area=propia).distinct() if propia else qs.none()

    def get_readonly_fields(self, request, obj=None):
        """Un jefe de área no puede ascender a nadie, ni a sí mismo."""
        ro = list(super().get_readonly_fields(request, obj))
        if not es_admin(request.user):
            ro += ["is_superuser", "is_staff", "groups"]
        return ro


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "jefe_texto", "total_miembros", "total_terminos", "activa"]
    list_filter = ["activa"]
    search_fields = ["nombre", "descripcion"]
    autocomplete_fields = ["jefe"]
    readonly_fields = ["creado_en", "actualizado_en", "creado_por", "actualizado_por"]

    @admin.display(description="Jefe")
    def jefe_texto(self, obj):
        if not obj.jefe:
            return format_html('<span style="color:#c00">sin jefe</span>')
        return obj.jefe.get_full_name() or obj.jefe.username

    @admin.display(description="Miembros")
    def total_miembros(self, obj):
        return obj.miembros.count()

    @admin.display(description="Términos")
    def total_terminos(self, obj):
        return obj.terminos.count()

    def has_add_permission(self, request):
        return es_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return es_admin(request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(TipoIdentificacion)
class TipoIdentificacionAdmin(admin.ModelAdmin):
    list_display = ["abreviatura", "nombre"]
    search_fields = ["nombre", "abreviatura"]

    def has_add_permission(self, request):
        return es_admin(request.user)


@admin.register(UsuarioArea)
class UsuarioAreaAdmin(admin.ModelAdmin):
    list_display = ["usuario", "area", "creado_en"]
    list_filter = ["area"]
    search_fields = ["usuario__username", "usuario__first_name", "usuario__last_name", "area__nombre"]
    autocomplete_fields = ["usuario", "area"]

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("usuario", "area")
        if es_admin(request.user):
            return qs
        propia = area_a_cargo(request.user)
        return qs.filter(area=propia) if propia else qs.none()


admin.site.site_header = "S.A.A.I — Administración"
admin.site.site_title = "S.A.A.I"
admin.site.index_title = "Sistema de Ayuda Automatizado para la Inducción"
