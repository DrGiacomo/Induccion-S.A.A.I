"""
Piezas compartidas por todas las apps.

`comun` no es una app de Django: es un paquete de Python normal. Los modelos
abstractos no necesitan pertenecer a una app, y ponerlos aquí evita que
`contenido` tenga que importar de `usuarios` solo para heredar unos campos.
"""

from django.conf import settings
from django.db import models


class ModeloBase(models.Model):
    """
    Marcas de auditoría para todo lo que se pueda crear o editar.

    Por qué existe (P0.7): en el modelo anterior **ningún** modelo guardaba
    fechas ni autor. Eso tenía dos consecuencias, y la segunda es la grave:

    1. No se sabía quién subió qué ni cuándo, en un sistema donde el jefe de
       área es el responsable de abastecer su estantería.
    2. **Sin fechas no hay dashboard posible.** No se puede graficar en el
       tiempo lo que no registra tiempo, y el histórico anterior a añadir el
       campo queda en blanco para siempre. Por eso va desde el día uno y no
       "cuando haga falta".
    """

    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado el",
        db_index=True,
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última modificación",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_creados",
        verbose_name="Creado por",
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_actualizados",
        verbose_name="Actualizado por",
    )

    class Meta:
        abstract = True


class EstadoContenido(models.TextChoices):
    """
    Ciclo de vida de todo lo consultable.

    `ARCHIVADO` existe para cumplir P7 (nada se borra en silencio): el
    contenido que deja de valer se marca, no desaparece. Si desapareciera,
    un procedimiento podría citar un término que ya no existe y nadie sabría
    por qué.
    """

    BORRADOR = "borrador", "Borrador"
    PUBLICADO = "publicado", "Publicado"
    ARCHIVADO = "archivado", "Archivado"


class ContenidoPublicable(ModeloBase):
    """
    Base de todo lo que un jefe de área cura y publica.

    El estado arranca en BORRADOR **a propósito**. Es P1 convertido en un
    valor por defecto: lo que propone la IA al ingerir un documento nace
    invisible, y solo un humano puede publicarlo. Si el defecto fuera
    PUBLICADO, bastaría un olvido para que una definición inventada llegara
    a un recién llegado.
    """

    estado = models.CharField(
        max_length=12,
        choices=EstadoContenido.choices,
        default=EstadoContenido.BORRADOR,
        db_index=True,
        verbose_name="Estado",
    )

    class Meta:
        abstract = True

    @property
    def es_visible(self) -> bool:
        """Solo lo publicado se puede consultar. Borradores y archivados, no."""
        return self.estado == EstadoContenido.PUBLICADO
