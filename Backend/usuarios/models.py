"""
Identidad y estructura organizativa.

Aquí vive quién es cada persona y dónde encaja. Los permisos que se derivan
de eso (Admin / Jefe de Área / Trabajador) se apoyan en los grupos nativos
de Django, no se reimplementan (P8).
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from comun.modelos import ModeloBase


class TipoIdentificacion(models.Model):
    """
    Cédula de ciudadanía, tarjeta de identidad, cédula de extranjería…

    Arregla un fallo que venía desde el diagrama en papel: antes existía el
    *tipo* de identificación y **no existía el número**. Era un campo que
    describía algo que no se guardaba en ninguna parte.
    """

    nombre = models.CharField(
        max_length=60,
        unique=True,
        verbose_name="Tipo de identificación",
    )
    abreviatura = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Abreviatura",
        help_text="CC, TI, CE, PA…",
    )

    class Meta:
        db_table = "tipo_identificacion"
        verbose_name = "Tipo de identificación"
        verbose_name_plural = "Tipos de identificación"
        ordering = ["nombre"]

    def __str__(self):
        return self.abreviatura


class Usuario(AbstractUser):
    """
    El usuario del sistema, con sus datos personales **dentro**.

    Antes esto estaba partido en dos: el `User` de Django más un `perfildb`
    colgando por OneToOne. Funcionaba, pero obligaba a un JOIN en cada
    consulta y dejaba los datos de la persona repartidos en dos tablas.

    Django recomienda declarar un modelo propio desde el primer día porque
    cambiarlo después es de lo más doloroso que tiene el framework: las
    tablas de permisos quedan apuntando al modelo viejo. Se hizo en P0.6,
    con la base vacía, que es el momento más barato que va a existir.

    Nadie se registra solo: las credenciales las entrega un administrador o
    el jefe del área (F-NO-14). Por eso `debe_cambiar_password` arranca en
    True: quien entregó la contraseña también la conoce.
    """

    tipo_identificacion = models.ForeignKey(
        TipoIdentificacion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="Tipo de identificación",
    )
    numero_identificacion = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Número de identificación",
        validators=[RegexValidator(r"^[A-Za-z0-9\-]+$", "Solo letras, números y guiones.")],
    )
    telefono = models.CharField(
        max_length=25,
        blank=True,
        verbose_name="Teléfono",
        help_text="Con indicativo si aplica. Ej: +57 300 000 0000",
    )
    debe_cambiar_password = models.BooleanField(
        default=True,
        verbose_name="Debe cambiar la contraseña",
        help_text="Se fuerza el cambio en el primer ingreso porque las credenciales se entregan.",
    )
    cargo = models.ForeignKey(
        "contenido.Cargo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="personas",
        verbose_name="Cargo",
        help_text=(
            "El puesto en la empresa. De aquí sale lo que esta persona debería "
            "leer al entrar, sin construir rutas formativas."
        ),
    )

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["first_name", "last_name", "username"]

    def __str__(self):
        nombre = self.get_full_name().strip()
        return nombre or self.username

    @property
    def identificacion(self) -> str:
        """`CC 1020304050`, o cadena vacía si no se ha registrado."""
        if not self.numero_identificacion:
            return ""
        prefijo = self.tipo_identificacion.abreviatura if self.tipo_identificacion else ""
        return f"{prefijo} {self.numero_identificacion}".strip()


class Area(ModeloBase):
    """
    Unidad organizativa que posee conocimiento y controla quién accede a él.

    En la metáfora del proyecto: un pasillo de la biblioteca. El jefe del
    área es quien abastece esa estantería.

    `jefe` es OneToOne y no ForeignKey porque se decidió que un área tiene un
    solo jefe y un jefe responde por una sola área (`D4`). El OneToOne impone
    las dos mitades de esa regla en la base de datos, no en el código.
    """

    nombre = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="Nombre del área",
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
    )
    jefe = models.OneToOneField(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="area_a_cargo",
        verbose_name="Jefe del área",
        help_text="Solo un administrador puede nombrarlo.",
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        db_table = "area"
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UsuarioArea(ModeloBase):
    """
    A qué áreas pertenece una persona. Una puede pertenecer a varias.

    `UniqueConstraint` no es un adorno: sin él se puede asignar quince veces
    la misma área a la misma persona, que es exactamente lo que permitían las
    tablas `userarea` y `userrol` del modelo anterior. Una tabla de relación
    sin restricción de unicidad deja de ser una relación y se vuelve un log.
    """

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="areas_asignadas",
        verbose_name="Usuario",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name="miembros",
        verbose_name="Área",
    )

    class Meta:
        db_table = "usuario_area"
        verbose_name = "Área del usuario"
        verbose_name_plural = "Áreas de los usuarios"
        ordering = ["usuario", "area"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "area"],
                name="usuario_area_unica",
            )
        ]

    def __str__(self):
        return f"{self.usuario} — {self.area}"
