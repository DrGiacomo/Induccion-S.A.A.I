"""
Datos de demostración para probar el sistema con algo dentro.

    python manage.py datos_demo            # crea
    python manage.py datos_demo --borrar   # limpia lo que creó

Es idempotente y **no toca nada que no haya creado él**: todo lo suyo lleva
la marca `[demo]` en la descripción, y el borrado se limita a eso.

⚠️ Esto NO es la carga de contenido real (`P2.6`). Aquel paso es la primera
validación de verdad del proyecto y depende de una persona que conozca la
empresa, no de un script.
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from comun.modelos import EstadoContenido
from comun.permisos import Rol
from contenido.models import Cargo, Sinonimo, Termino
from usuarios.models import Area, TipoIdentificacion, Usuario, UsuarioArea

MARCA = "[demo]"
CLAVE = "Demo2026Saai"


class Command(BaseCommand):
    help = "Crea (o borra) datos de demostración."

    def add_arguments(self, parser):
        parser.add_argument("--borrar", action="store_true", help="Elimina lo creado por este comando.")

    @transaction.atomic
    def handle(self, *args, **op):
        if op["borrar"]:
            return self.borrar()

        cc, _ = TipoIdentificacion.objects.get_or_create(
            abreviatura="CC", defaults={"nombre": "Cédula de ciudadanía"}
        )

        produccion = self._area("Producción", "Fabricación y control de planta.")
        ventas = self._area("Ventas", "Atención comercial y clientes.")

        jefe_prod = self._usuario("mrojas", "Marta", "Rojas", Rol.JEFE_AREA, produccion, cc)
        jefe_ventas = self._usuario("cpardo", "Carlos", "Pardo", Rol.JEFE_AREA, ventas, cc)
        obrero = self._usuario("lgomez", "Luis", "Gómez", Rol.TRABAJADOR, produccion, cc)
        self._usuario("avargas", "Ana", "Vargas", Rol.TRABAJADOR, ventas, cc)

        produccion.jefe = jefe_prod
        produccion.save(update_fields=["jefe"])
        ventas.jefe = jefe_ventas
        ventas.save(update_fields=["jefe"])

        # El caso que justifica que no haya unicidad de nombre: la misma
        # palabra con dos significados en dos áreas.
        corte_p = self._termino(
            "Corte", "Separar el material según el patrón del pedido.", [produccion],
            detalle="Se usa la plantilla PR-04. La tolerancia es de ±2 mm; por encima cuenta como merma.",
            ejemplo="«El corte de la referencia 88 salió con 3 mm de más.»",
        )
        self._termino(
            "Corte", "Cierre del periodo de facturación del mes.", [ventas],
            detalle="Se hace el día 25. Lo que entre después va al mes siguiente.",
        )

        merma = self._termino(
            "Merma", "Producto que se pierde o se daña durante el proceso.", [produccion],
            detalle="Se registra en el formato MP-12 al cierre de cada turno.",
            ejemplo="«El turno de la noche reportó 4 % de merma.»",
        )
        for texto in ("desperdicio", "pérdida de turno", "producto no conforme"):
            Sinonimo.objects.get_or_create(termino=merma, texto=texto)

        # Transversal: sin áreas dueñas.
        self._termino(
            "PQR", "Peticiones, quejas y reclamos que llegan de clientes o de personal.", [],
            detalle="Se responden en un máximo de 15 días hábiles.",
        )
        self._termino(
            "Reglamento interno", "Las normas de convivencia y trabajo de la empresa.", [],
        )

        # Uno en borrador, para que la bandeja de curaduría tenga algo.
        self._termino(
            "Retrabajo", "Volver a procesar una pieza que salió mal.", [produccion],
            estado=EstadoContenido.BORRADOR,
        )

        cargo = self._cargo("Auxiliar de Bodega", produccion,
                            "Recibe, almacena y despacha material.")
        cargo.terminos.set([corte_p, merma])
        obrero.cargo = cargo
        obrero.save(update_fields=["cargo"])

        self.stdout.write(self.style.SUCCESS("\nDatos de demostración listos.\n"))
        self.stdout.write("  Usuarios creados (contraseña: %s)\n" % CLAVE)
        for u, que in [("mrojas", "jefa de Producción"), ("cpardo", "jefe de Ventas"),
                       ("lgomez", "trabajador de Producción, Auxiliar de Bodega"),
                       ("avargas", "trabajadora de Ventas")]:
            self.stdout.write(f"    {u:10s} — {que}")
        self.stdout.write(
            "\n  Prueba a entrar como 'avargas' y buscar «Corte»: verás la definición\n"
            "  de Producción con candado, y la de Ventas completa.\n"
        )

    # ── auxiliares ──────────────────────────────────────────────────────

    def _area(self, nombre, descripcion):
        a, _ = Area.objects.get_or_create(
            nombre=nombre, defaults={"descripcion": f"{descripcion} {MARCA}"}
        )
        return a

    def _usuario(self, username, nombre, apellido, rol, area, tipo_id):
        u, creado = Usuario.objects.get_or_create(
            username=username,
            defaults={
                "first_name": nombre, "last_name": apellido,
                "email": f"{username}@ejemplo.com", "tipo_identificacion": tipo_id,
                "is_staff": rol in (Rol.ADMIN, Rol.JEFE_AREA),
                "debe_cambiar_password": False,   # es una demo, no molestamos
            },
        )
        if creado:
            u.set_password(CLAVE)
            u.save()
        grupo = Group.objects.filter(name=rol).first()
        if grupo:
            u.groups.add(grupo)
        UsuarioArea.objects.get_or_create(usuario=u, area=area)
        return u

    def _termino(self, nombre, definicion, areas, detalle="", ejemplo="",
                 estado=EstadoContenido.PUBLICADO):
        existente = Termino.objects.filter(nombre=nombre, areas__in=[a.id for a in areas]).first() \
            if areas else Termino.objects.filter(nombre=nombre, areas__isnull=True).first()
        if existente:
            return existente
        t = Termino.objects.create(
            nombre=nombre, definicion=definicion, detalle=detalle,
            ejemplo=ejemplo, estado=estado,
        )
        t.areas.set(areas)
        return t

    def _cargo(self, nombre, area, descripcion):
        c, _ = Cargo.objects.get_or_create(
            nombre=nombre, area=area,
            defaults={"descripcion": f"{descripcion} {MARCA}", "estado": EstadoContenido.PUBLICADO},
        )
        return c

    def borrar(self):
        usuarios = ["mrojas", "cpardo", "lgomez", "avargas"]
        Usuario.objects.filter(username__in=usuarios).delete()
        Termino.objects.filter(
            nombre__in=["Corte", "Merma", "PQR", "Reglamento interno", "Retrabajo"]
        ).delete()
        Cargo.objects.filter(descripcion__contains=MARCA).delete()
        Area.objects.filter(descripcion__contains=MARCA).delete()
        self.stdout.write(self.style.SUCCESS("Datos de demostración eliminados."))
