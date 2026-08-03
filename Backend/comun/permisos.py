"""
Roles del sistema y quién puede ver qué.

Los tres roles se apoyan en los **grupos nativos de Django** (P8). Django ya
tiene grupos, permisos y toda la maquinaria probada; reimplementarla a mano
sería gastar semanas en construir —con bugs propios— algo que ya viene hecho.

Lo que Django **no** trae, y por eso sí se escribe aquí, es el filtro por
área: que un trabajador de Ventas no alcance el contenido de Producción.
Eso es específico de este proyecto.

⚠️ Las fugas de permisos no avisan. Un permiso roto **funciona
perfectamente**, solo que para la persona equivocada. Por eso todo lo de
este archivo se prueba en `P2.7` con una suite que debe fallar si alguien
quita el filtro.
"""

from rest_framework import permissions


class Rol:
    """Los tres roles del sistema. Son grupos de Django, no una tabla propia."""

    ADMIN = "Administrador"
    JEFE_AREA = "Jefe de Área"
    TRABAJADOR = "Trabajador"

    TODOS = (ADMIN, JEFE_AREA, TRABAJADOR)


# ── Preguntas sobre el usuario ──────────────────────────────────────────

def es_admin(usuario) -> bool:
    """Un superusuario de Django cuenta como administrador."""
    if not usuario or not usuario.is_authenticated:
        return False
    return usuario.is_superuser or usuario.groups.filter(name=Rol.ADMIN).exists()


def es_jefe_de_area(usuario) -> bool:
    if not usuario or not usuario.is_authenticated:
        return False
    return usuario.groups.filter(name=Rol.JEFE_AREA).exists()


def area_a_cargo(usuario):
    """El área que dirige, o None. Un jefe responde por una sola área (D4)."""
    if not usuario or not usuario.is_authenticated:
        return None
    return getattr(usuario, "area_a_cargo", None)


def ids_areas_del_usuario(usuario) -> set:
    """
    Los ids de las áreas a las que pertenece, más la que dirige si es jefe.

    Se devuelve un conjunto de ids y no objetos porque esto se usa dentro de
    filtros de consulta, en la ruta caliente del buscador. Traer los objetos
    completos aquí sería un JOIN por cada búsqueda.
    """
    if not usuario or not usuario.is_authenticated:
        return set()
    ids = set(usuario.areas_asignadas.values_list("area_id", flat=True))
    propia = area_a_cargo(usuario)
    if propia:
        ids.add(propia.id)
    return ids


def puede_curar_area(usuario, area_id) -> bool:
    """
    ¿Puede crear, editar y publicar contenido de esta área?

    Solo el administrador y el jefe de esa área concreta. Pertenecer a un
    área te deja consultarla, no abastecerla.
    """
    if es_admin(usuario):
        return True
    propia = area_a_cargo(usuario)
    return bool(propia and propia.id == int(area_id))


# ── Clases de permiso para la API ───────────────────────────────────────

class EsAdmin(permissions.BasePermission):
    message = "Solo un administrador puede hacer esto."

    def has_permission(self, request, view):
        return es_admin(request.user)


class EsAdminOJefeDeArea(permissions.BasePermission):
    message = "Solo un administrador o un jefe de área puede hacer esto."

    def has_permission(self, request, view):
        return es_admin(request.user) or es_jefe_de_area(request.user)


class LecturaParaTodosEscrituraParaCuradores(permissions.BasePermission):
    """
    Cualquiera con sesión puede consultar; solo curadores pueden modificar.

    El filtro de *qué* puede consultar cada quien no vive aquí: vive en el
    queryset de cada vista. Esta clase decide **si puede escribir**, no
    **qué puede leer**. Mezclar las dos cosas es como se escapan las fugas.
    """

    message = "No tienes permiso para modificar este contenido."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return es_admin(request.user) or es_jefe_de_area(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if es_admin(request.user):
            return True
        propia = area_a_cargo(request.user)
        if not propia:
            return False
        # El contenido transversal (sin áreas dueñas) solo lo toca el admin:
        # es de todos, así que no puede quedar bajo el criterio de un área.
        areas = getattr(obj, "areas", None)
        if areas is None:
            return getattr(obj, "area_id", None) == propia.id
        ids = set(areas.values_list("id", flat=True))
        return bool(ids) and propia.id in ids
