"""
Pruebas de permisos — la primera suite del proyecto.

**Por qué existe, y por qué es esta y no otra.**

Un permiso roto no se ve. La pantalla funciona, el endpoint responde 200, no
queda rastro en los logs. Simplemente le está enseñando a la persona
equivocada algo que no le corresponde. Es el único tipo de fallo del proyecto
que no se detecta mirando, y por eso es el único que obliga a tener pruebas.

**El criterio:** si alguien quita el filtro de área de un endpoint, estas
pruebas tienen que fallar. Una prueba que no falla cuando rompes lo que
vigila no está vigilando nada.

    python manage.py test
"""

from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from comun.modelos import EstadoContenido
from comun.permisos import Rol
from contenido.models import Documento, Termino

from .models import Area, Usuario, UsuarioArea


class BasePermisos(APITestCase):
    """Una empresa mínima: dos áreas, un jefe cada una, dos trabajadores."""

    @classmethod
    def setUpTestData(cls):
        for nombre in Rol.TODOS:
            Group.objects.get_or_create(name=nombre)

        cls.produccion = Area.objects.create(nombre="Producción")
        cls.ventas = Area.objects.create(nombre="Ventas")

        cls.admin = cls._crear("admin", Rol.ADMIN, superusuario=True)
        cls.jefe_prod = cls._crear("jefe_prod", Rol.JEFE_AREA, area=cls.produccion)
        cls.jefe_ventas = cls._crear("jefe_ventas", Rol.JEFE_AREA, area=cls.ventas)
        cls.obrero = cls._crear("obrero", Rol.TRABAJADOR, area=cls.produccion)
        cls.vendedor = cls._crear("vendedor", Rol.TRABAJADOR, area=cls.ventas)

        cls.produccion.jefe = cls.jefe_prod
        cls.produccion.save()
        cls.ventas.jefe = cls.jefe_ventas
        cls.ventas.save()

        # "Corte" significa cosas distintas en cada área. Las dos conviven.
        cls.corte_prod = cls._termino("Corte", "Cortar el material.", cls.produccion,
                                      detalle="Se calcula con la plantilla PR-04.")
        cls.corte_vta = cls._termino("Corte", "Cierre del periodo de ventas.", cls.ventas)

        # Transversal: sin áreas dueñas, lo ve todo el mundo.
        cls.reglamento = cls._termino("Reglamento interno", "Normas de la empresa.", None)

        # De Producción y con la definición marcada como NO pública: no debe
        # existir para nadie de fuera, ni siquiera con candado.
        cls.secreto = cls._termino("Fórmula X", "Composición reservada.", cls.produccion,
                                   publica=False)

        cls.borrador = cls._termino("Merma", "Producto perdido.", cls.produccion,
                                    estado=EstadoContenido.BORRADOR)

        cls.doc_prod = Documento.objects.create(
            nombre="Procedimiento de corte", archivo="documentos/prueba.pdf",
            estado=EstadoContenido.PUBLICADO,
        )
        cls.doc_prod.areas.add(cls.produccion)

    @classmethod
    def _crear(cls, username, rol, area=None, superusuario=False):
        u = Usuario.objects.create_user(
            username=username, password="ClaveDePrueba123", first_name=username.title(),
            is_superuser=superusuario, is_staff=superusuario,
        )
        u.groups.add(Group.objects.get(name=rol))
        if area:
            UsuarioArea.objects.create(usuario=u, area=area)
        return u

    @classmethod
    def _termino(cls, nombre, definicion, area, detalle="", publica=True,
                 estado=EstadoContenido.PUBLICADO):
        t = Termino.objects.create(
            nombre=nombre, definicion=definicion, detalle=detalle,
            definicion_es_publica=publica, estado=estado,
        )
        if area:
            t.areas.add(area)
        return t

    def entrar(self, usuario):
        self.client.force_authenticate(user=usuario)


class SinSesion(BasePermisos):
    """Nada se ve sin iniciar sesión. Ni siquiera lo público."""

    def test_listar_terminos_exige_sesion(self):
        r = self.client.get("/api/terminos/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_detalle_por_id_exige_sesion(self):
        r = self.client.get(f"/api/terminos/{self.corte_prod.id}/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_usuarios_exige_sesion(self):
        r = self.client.get("/api/usuarios/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_borrar_exige_sesion(self):
        r = self.client.delete(f"/api/terminos/{self.corte_prod.id}/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.corte_prod.refresh_from_db()
        self.assertEqual(self.corte_prod.estado, EstadoContenido.PUBLICADO)


class VisibilidadPorArea(BasePermisos):
    """El corazón del asunto: quién ve qué."""

    def test_el_transversal_lo_ve_todo_el_mundo(self):
        for usuario in (self.obrero, self.vendedor, self.jefe_ventas):
            self.entrar(usuario)
            r = self.client.get(f"/api/terminos/{self.reglamento.id}/")
            self.assertEqual(r.status_code, 200, f"{usuario} no vio el transversal")
            self.assertFalse(r.data["acceso_restringido"])

    def test_de_mi_area_veo_el_detalle(self):
        self.entrar(self.obrero)
        r = self.client.get(f"/api/terminos/{self.corte_prod.id}/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["acceso_restringido"])
        self.assertEqual(r.data["detalle"], "Se calcula con la plantilla PR-04.")

    def test_de_otra_area_veo_la_definicion_pero_NO_el_detalle(self):
        """El candado de P4: se ve que existe, no lo que dice."""
        self.entrar(self.vendedor)
        r = self.client.get(f"/api/terminos/{self.corte_prod.id}/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["acceso_restringido"])
        self.assertEqual(r.data["definicion"], "Cortar el material.")
        # ⚠️ La clave se ELIMINA, no se vacía. Si esto falla, el detalle está
        #    viajando al navegador aunque la interfaz no lo pinte.
        self.assertNotIn("detalle", r.data)
        self.assertNotIn("ejemplo", r.data)

    def test_el_candado_dice_a_quien_pedir_acceso(self):
        """Sin esto P4 no se cumple: el usuario queda en un callejón sin salida."""
        self.entrar(self.vendedor)
        r = self.client.get(f"/api/terminos/{self.corte_prod.id}/")
        encargado = r.data["encargado"]
        self.assertIsNotNone(encargado)
        self.assertEqual(encargado["nombre"], self.jefe_prod.get_full_name())
        self.assertIn("Producción", encargado["areas"])

    def test_lo_no_publico_de_otra_area_NO_EXISTE(self):
        """Ni con candado: no aparece ni por lista ni por id."""
        self.entrar(self.vendedor)
        self.assertEqual(self.client.get(f"/api/terminos/{self.secreto.id}/").status_code, 404)

        r = self.client.get("/api/terminos/")
        nombres = [t["nombre"] for t in r.data["results"]]
        self.assertNotIn("Fórmula X", nombres)

    def test_los_borradores_no_se_ven_desde_fuera(self):
        """P1: lo que no aprobó un humano no llega a nadie."""
        self.entrar(self.vendedor)
        self.assertEqual(self.client.get(f"/api/terminos/{self.borrador.id}/").status_code, 404)
        self.entrar(self.obrero)
        self.assertEqual(self.client.get(f"/api/terminos/{self.borrador.id}/").status_code, 404)

    def test_el_jefe_SI_ve_los_borradores_de_su_area(self):
        """Si no, no podría revisar lo que la ingesta le proponga en la Fase 4."""
        self.entrar(self.jefe_prod)
        self.assertEqual(self.client.get(f"/api/terminos/{self.borrador.id}/").status_code, 200)

    def test_el_admin_lo_ve_todo(self):
        self.entrar(self.admin)
        for t in (self.corte_prod, self.secreto, self.borrador):
            self.assertEqual(self.client.get(f"/api/terminos/{t.id}/").status_code, 200)

    def test_mismo_nombre_en_dos_areas_conviven(self):
        self.entrar(self.admin)
        r = self.client.get("/api/terminos/?search=Corte")
        cortes = [t for t in r.data["results"] if t["nombre"] == "Corte"]
        self.assertEqual(len(cortes), 2)

    def test_el_archivo_de_otra_area_no_viaja(self):
        self.entrar(self.vendedor)
        r = self.client.get(f"/api/documentos/{self.doc_prod.id}/")
        self.assertEqual(r.status_code, 200)          # se ve que existe…
        self.assertTrue(r.data["acceso_restringido"])
        self.assertIsNone(r.data["archivo"])          # …pero no se descarga


class Escritura(BasePermisos):
    """Quién puede tocar qué."""

    def test_un_trabajador_no_puede_crear_contenido(self):
        self.entrar(self.obrero)
        r = self.client.post("/api/terminos/", {"nombre": "X", "definicion": "Y"})
        self.assertEqual(r.status_code, 403)

    def test_un_jefe_no_puede_crear_en_area_ajena(self):
        self.entrar(self.jefe_ventas)
        r = self.client.post("/api/terminos/", {
            "nombre": "Intruso", "definicion": "No debería entrar",
            "areas": [self.produccion.id],
        })
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Termino.objects.filter(nombre="Intruso").exists())

    def test_un_jefe_no_puede_crear_contenido_transversal(self):
        """Lo transversal es de todos: solo el administrador decide sobre ello."""
        self.entrar(self.jefe_ventas)
        r = self.client.post("/api/terminos/", {"nombre": "Global", "definicion": "De todos"})
        self.assertEqual(r.status_code, 400)

    def test_un_jefe_no_puede_publicar_contenido_ajeno(self):
        self.entrar(self.jefe_ventas)
        r = self.client.post(f"/api/terminos/{self.borrador.id}/publicar/")
        self.assertIn(r.status_code, (403, 404))
        self.borrador.refresh_from_db()
        self.assertEqual(self.borrador.estado, EstadoContenido.BORRADOR)

    def test_borrar_archiva_pero_no_borra(self):
        """P7: nada se borra en silencio."""
        self.entrar(self.jefe_prod)
        r = self.client.delete(f"/api/terminos/{self.corte_prod.id}/")
        self.assertEqual(r.status_code, 200)
        self.corte_prod.refresh_from_db()
        self.assertEqual(self.corte_prod.estado, EstadoContenido.ARCHIVADO)
        self.assertTrue(Termino.objects.filter(pk=self.corte_prod.pk).exists())


class EscaladaDePrivilegios(BasePermisos):
    """Los intentos de subirse el rango llamando a la API a mano."""

    def test_un_jefe_no_puede_nombrar_jefes(self):
        self.entrar(self.jefe_ventas)
        r = self.client.post(f"/api/areas/{self.ventas.id}/nombrar_jefe/",
                             {"usuario_id": self.vendedor.id})
        self.assertEqual(r.status_code, 403)

    def test_un_jefe_no_puede_crear_administradores(self):
        self.entrar(self.jefe_ventas)
        r = self.client.post("/api/usuarios/", {
            "username": "colado", "password": "ClaveMuyLarga987",
            "first_name": "Colado", "rol": Rol.ADMIN,
        })
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Usuario.objects.filter(username="colado").exists())

    def test_un_jefe_no_puede_crear_gente_en_area_ajena(self):
        self.entrar(self.jefe_ventas)
        r = self.client.post("/api/usuarios/", {
            "username": "infiltrado", "password": "ClaveMuyLarga987",
            "first_name": "Infiltrado", "areas": [self.produccion.id],
        })
        self.assertEqual(r.status_code, 400)

    def test_un_jefe_solo_ve_a_la_gente_de_su_area(self):
        self.entrar(self.jefe_ventas)
        r = self.client.get("/api/usuarios/")
        nombres = [u["username"] for u in r.data["results"]]
        self.assertIn("vendedor", nombres)
        self.assertNotIn("obrero", nombres)

    def test_un_trabajador_no_llega_al_listado_de_usuarios(self):
        self.entrar(self.obrero)
        self.assertEqual(self.client.get("/api/usuarios/").status_code, 403)

    def test_un_jefe_no_puede_crear_areas(self):
        self.entrar(self.jefe_prod)
        r = self.client.post("/api/areas/", {"nombre": "Área inventada"})
        self.assertEqual(r.status_code, 403)


class Autenticacion(BasePermisos):
    def test_login_correcto(self):
        r = self.client.post("/api/auth/login/",
                             {"username": "obrero", "password": "ClaveDePrueba123"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["usuario"]["username"], "obrero")

    def test_login_incorrecto_no_revela_si_el_usuario_existe(self):
        """Mismo mensaje en los dos casos, o se filtra qué usuarios hay."""
        r1 = self.client.post("/api/auth/login/", {"username": "obrero", "password": "mala"})
        r2 = self.client.post("/api/auth/login/", {"username": "fantasma", "password": "mala"})
        self.assertEqual(r1.status_code, 401)
        self.assertEqual(r2.status_code, 401)
        self.assertEqual(r1.data["detail"], r2.data["detail"])

    def test_un_usuario_desactivado_no_entra(self):
        self.obrero.is_active = False
        self.obrero.save()
        r = self.client.post("/api/auth/login/",
                             {"username": "obrero", "password": "ClaveDePrueba123"})
        self.assertIn(r.status_code, (401, 403))

    def test_desactivar_borra_el_historial_personal(self):
        """Ley 1581/2012: los datos personales se guardan mientras haya finalidad."""
        from busqueda.models import Consulta

        Consulta.objects.create(usuario=self.vendedor, texto="merma", num_resultados=0)
        self.assertEqual(Consulta.objects.filter(usuario=self.vendedor).count(), 1)

        self.entrar(self.admin)
        r = self.client.delete(f"/api/usuarios/{self.vendedor.id}/")
        self.assertEqual(r.status_code, 200)

        self.vendedor.refresh_from_db()
        self.assertFalse(self.vendedor.is_active)                                # desactivado…
        self.assertTrue(Usuario.objects.filter(pk=self.vendedor.pk).exists())    # …no borrado
        self.assertEqual(Consulta.objects.filter(usuario=self.vendedor).count(), 0)

    def test_no_puedo_desactivarme_a_mi_mismo(self):
        self.entrar(self.admin)
        r = self.client.delete(f"/api/usuarios/{self.admin.id}/")
        self.assertEqual(r.status_code, 400)

    def test_cambiar_password_apaga_la_obligacion(self):
        self.entrar(self.obrero)
        self.assertTrue(self.obrero.debe_cambiar_password)
        r = self.client.post("/api/auth/cambiar-password/", {
            "password_actual": "ClaveDePrueba123",
            "password_nueva": "OtraClaveLarga456",
        })
        self.assertEqual(r.status_code, 200)
        self.obrero.refresh_from_db()
        self.assertFalse(self.obrero.debe_cambiar_password)
        self.assertTrue(self.obrero.check_password("OtraClaveLarga456"))

    def test_no_se_puede_repetir_la_misma_password(self):
        self.entrar(self.obrero)
        r = self.client.post("/api/auth/cambiar-password/", {
            "password_actual": "ClaveDePrueba123",
            "password_nueva": "ClaveDePrueba123",
        })
        self.assertEqual(r.status_code, 400)


class InduccionPorCargo(BasePermisos):
    """La ruta de inducción que emerge del cargo, sin construir un LMS."""

    def test_sin_cargo_avisa_en_vez_de_fallar(self):
        self.entrar(self.obrero)
        r = self.client.get("/api/cargos/mi_induccion/")
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.data["cargo"])
        self.assertIn("cargo", r.data["mensaje"].lower())

    def test_con_cargo_devuelve_lo_que_debe_leer(self):
        from contenido.models import Cargo

        cargo = Cargo.objects.create(nombre="Auxiliar de Bodega", area=self.produccion,
                                     estado=EstadoContenido.PUBLICADO)
        cargo.terminos.add(self.corte_prod, self.reglamento)
        self.obrero.cargo = cargo
        self.obrero.save()

        self.entrar(self.obrero)
        r = self.client.get("/api/cargos/mi_induccion/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["cargo"]["nombre"], "Auxiliar de Bodega")
        self.assertEqual(len(r.data["terminos"]), 2)
