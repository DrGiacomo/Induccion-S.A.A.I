"""
El rastro: qué buscó cada quien, y qué busca la gente que no encuentra.

Dos tipos de registro que se comportan distinto **a propósito**:

- `Consulta` es **personal** y se borra cuando alguien deja la empresa.
- Los contadores son **anónimos** y sobreviven para siempre.

Si se borrara todo al desactivar a una persona, cada salida se llevaría un
pedazo de las estadísticas y el dashboard de la Fase 5 mentiría. Si se
guardara todo, se estarían reteniendo datos personales de alguien que ya no
tiene relación con la empresa — lo que la Ley 1581 de 2012 no permite. La
separación resuelve las dos cosas.
"""

from django.conf import settings
from django.db import models

from contenido.models import Termino


class Consulta(models.Model):
    """
    Historial personal de búsquedas.

    Sirve para que alguien vuelva sobre lo que investigó ayer, que es una de
    las razones por las que el sistema pide iniciar sesión.

    `on_delete=CASCADE` es deliberado: al eliminar el usuario desaparece su
    historial. No es un descuido, es el requisito.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consultas",
        verbose_name="Usuario",
    )
    texto = models.CharField(max_length=300, verbose_name="Lo que buscó")
    num_resultados = models.PositiveIntegerField(default=0, verbose_name="Resultados")
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Cuándo")

    class Meta:
        db_table = "consulta"
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["usuario", "-creado_en"], name="consulta_usuario_idx"),
        ]

    def __str__(self):
        return f"{self.usuario}: «{self.texto}»"


class ContadorTermino(models.Model):
    """
    Cuántas veces se ha consultado cada término. Sin dueño, anónimo.

    Alimenta la parte útil del dashboard: qué se consulta mucho —o sea, qué
    confunde a la gente— y qué no consulta nadie.
    """

    termino = models.OneToOneField(
        Termino,
        on_delete=models.CASCADE,
        related_name="contador",
        verbose_name="Término",
    )
    veces_consultado = models.PositiveIntegerField(default=0, verbose_name="Veces consultado")
    ultima_consulta = models.DateTimeField(null=True, blank=True, verbose_name="Última consulta")

    class Meta:
        db_table = "contador_termino"
        verbose_name = "Contador de término"
        verbose_name_plural = "Contadores de términos"
        ordering = ["-veces_consultado"]

    def __str__(self):
        return f"{self.termino.nombre}: {self.veces_consultado}"


class BusquedaSinResultado(models.Model):
    """
    Lo que la gente buscó y el sistema no supo responder.

    Este es el modelo más valioso del dashboard y el más fácil de no poner.
    Cada fila es **un hueco concreto en la biblioteca**, escrito por alguien
    que lo necesitaba de verdad: le dice al jefe de área qué documentar
    después, en vez de que lo adivine.

    Anónimo a propósito: interesa la palabra, no quién la escribió.
    """

    texto = models.CharField(max_length=300, unique=True, verbose_name="Lo que se buscó")
    veces = models.PositiveIntegerField(default=1, verbose_name="Veces")
    primera_vez = models.DateTimeField(auto_now_add=True, verbose_name="Primera vez")
    ultima_vez = models.DateTimeField(auto_now=True, verbose_name="Última vez")
    resuelto = models.BooleanField(
        default=False,
        verbose_name="Ya documentado",
        help_text="Se marca cuando alguien crea el término o el documento que faltaba.",
    )

    class Meta:
        db_table = "busqueda_sin_resultado"
        verbose_name = "Búsqueda sin resultado"
        verbose_name_plural = "Búsquedas sin resultado"
        ordering = ["-veces", "-ultima_vez"]

    def __str__(self):
        return f"«{self.texto}» ×{self.veces}"
