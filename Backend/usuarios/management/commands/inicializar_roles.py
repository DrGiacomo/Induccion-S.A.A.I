"""
Crea los tres roles del sistema como grupos nativos de Django.

    python manage.py inicializar_roles

Es idempotente: se puede correr las veces que haga falta. Al desplegar en
una empresa nueva, este comando y `createsuperuser` son lo único que hay
que ejecutar a mano.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from comun.permisos import Rol

# Qué puede hacer cada rol sobre cada modelo.
#
# ⚠️ Estos permisos son **por modelo, no por fila**. Django sabe decir "este
#    usuario puede editar términos"; no sabe decir "puede editar los términos
#    de Producción". Ese filtro es nuestro y vive en `ContenidoQuerySet` y en
#    las clases de `comun/permisos.py`.
#
#    Los dos niveles son necesarios y hacen cosas distintas: estos permisos
#    gobiernan el panel de administración de Django; el filtro por área
#    gobierna la API. Quitar cualquiera de los dos abre un hueco.

PERMISOS = {
    Rol.ADMIN: "__todos__",

    Rol.JEFE_AREA: [
        # Cura el contenido de su área. El filtro por fila lo pone el queryset.
        ("contenido", "termino",            ["add", "change", "view", "delete"]),
        ("contenido", "sinonimo",           ["add", "change", "view", "delete"]),
        ("contenido", "documento",          ["add", "change", "view", "delete"]),
        ("contenido", "cargo",              ["add", "change", "view", "delete"]),
        ("contenido", "mencionendocumento", ["add", "change", "view", "delete"]),
        # Da de alta gente en su área. NO puede nombrar jefes: eso es del admin.
        ("usuarios",  "usuario",            ["add", "change", "view"]),
        ("usuarios",  "usuarioarea",        ["add", "change", "view", "delete"]),
        ("usuarios",  "area",               ["view"]),
        ("usuarios",  "tipoidentificacion", ["view"]),
        ("busqueda",  "busquedasinresultado", ["view", "change"]),
        ("busqueda",  "contadortermino",    ["view"]),
    ],

    Rol.TRABAJADOR: [
        # Solo consulta. Lo que consulta lo decide el filtro por área.
        ("contenido", "termino",            ["view"]),
        ("contenido", "sinonimo",           ["view"]),
        ("contenido", "documento",          ["view"]),
        ("contenido", "cargo",              ["view"]),
        ("contenido", "mencionendocumento", ["view"]),
        ("usuarios",  "area",               ["view"]),
    ],
}


class Command(BaseCommand):
    help = "Crea o actualiza los grupos Administrador, Jefe de Área y Trabajador."

    @transaction.atomic
    def handle(self, *args, **opciones):
        todos = Permission.objects.all()

        for rol, reglas in PERMISOS.items():
            grupo, creado = Group.objects.get_or_create(name=rol)

            if reglas == "__todos__":
                grupo.permissions.set(todos)
                cuantos = todos.count()
            else:
                permisos = []
                for app, modelo, acciones in reglas:
                    for accion in acciones:
                        codigo = f"{accion}_{modelo}"
                        p = Permission.objects.filter(
                            codename=codigo, content_type__app_label=app
                        ).first()
                        if p:
                            permisos.append(p)
                        else:
                            self.stderr.write(f"  ! no existe el permiso {app}.{codigo}")
                grupo.permissions.set(permisos)
                cuantos = len(permisos)

            estado = "creado" if creado else "actualizado"
            self.stdout.write(f"  {rol:18s} {estado:12s} {cuantos:3d} permisos")

        self.stdout.write(self.style.SUCCESS("\nRoles listos."))
        self.stdout.write(
            "Recuerda: estos permisos son por MODELO. El filtro por área "
            "vive en el código y es el que impide que alguien de Ventas "
            "alcance el contenido de Producción."
        )
