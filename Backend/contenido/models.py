"""
El conocimiento de la empresa: vocabulario, estructura y evidencia.

La separación entre **Término** y **Documento** es la decisión más importante
de este archivo, y es lo que distingue un buscador de un archivador. Si
fueran la misma cosa —que es lo que pasaba antes, cuando solo existía
`repodb`— buscar "merma" devolvería *una lista de archivos que quizá la
mencionan*, no *una respuesta*.
"""

from django.db import models

from comun.modelos import ContenidoPublicable, EstadoContenido, ModeloBase
from comun.permisos import area_a_cargo, es_admin, ids_areas_del_usuario
from usuarios.models import Area


class ContenidoQuerySet(models.QuerySet):
    """
    El filtro de visibilidad por área. **Esto es P1.4 y es el corazón de los
    permisos del proyecto.**

    Se implementa como método de consulta y no como comprobación en la vista
    por una razón que no es de estilo: así el contenido prohibido **no sale
    del servidor**. Filtrar después —en el serializer o, peor, en el
    frontend— significa que el dato ya viajó, y entonces ya se filtró en el
    otro sentido de la palabra.

    Las tres reglas, en orden:

    1. **Administrador**: lo ve todo, incluidos los borradores.
    2. **Jefe de área**: todo lo suyo (borradores incluidos, porque los tiene
       que revisar) más lo que vería cualquiera.
    3. **Cualquiera con sesión**: solo lo publicado, y de eso:
       - lo transversal (sin áreas dueñas),
       - lo de sus propias áreas,
       - y lo de **otras** áreas **solo si su definición es pública** — que
         es lo que hace posible P4: verlo con candado y saber a quién pedir
         acceso, en vez de un vacío mudo.

    Lo que **nunca** aparece: contenido de otra área con la definición marcada
    como no pública. De eso ni se sabe que existe.
    """

    def visibles_para(self, usuario):
        if not usuario or not usuario.is_authenticated:
            return self.none()

        if es_admin(usuario):
            return self

        mis_areas = ids_areas_del_usuario(usuario)
        publicado = models.Q(estado=EstadoContenido.PUBLICADO)

        transversal = models.Q(areas__isnull=True)
        propio = models.Q(areas__in=mis_areas) if mis_areas else models.Q(pk__in=[])
        ajeno = self.model.filtro_ajeno_visible()

        visible = publicado & (transversal | propio | ajeno)

        propia = area_a_cargo(usuario)
        if propia:
            # El jefe ve TODO lo de su área, borradores incluidos: si no,
            # no podría revisar lo que la ingesta le propone (P1).
            visible |= models.Q(areas=propia)

        return self.filter(visible).distinct()

# La validación de archivos vive en `comun/archivos.py` (P1.9). Comprueba la
# extensión, el tamaño y —lo que de verdad importa— **los primeros bytes**:
# renombrar `virus.exe` a `manual.pdf` burla cualquier control por extensión,
# porque la extensión la escribe quien sube el archivo.
from comun.archivos import TAMANO_MAXIMO as TAMANO_MAXIMO_BYTES  # noqa: E402
from comun.archivos import validar_archivo  # noqa: E402


class CargoQuerySet(models.QuerySet):
    """
    Los cargos son más simples: pertenecen a **un** área, no a varias.

    Y son deliberadamente más abiertos. Saber que existe el cargo de
    "Auxiliar de Bodega" y qué hace no es información sensible — es
    justamente lo que un recién llegado necesita para entender la empresa.
    Lo que se protege son los términos y los documentos, no el organigrama.
    """

    def visibles_para(self, usuario):
        if not usuario or not usuario.is_authenticated:
            return self.none()
        if es_admin(usuario):
            return self
        visible = models.Q(estado=EstadoContenido.PUBLICADO)
        propia = area_a_cargo(usuario)
        if propia:
            visible |= models.Q(area=propia)     # el jefe ve sus borradores
        return self.filter(visible).distinct()


class Cargo(ContenidoPublicable):
    """
    Un puesto de la empresa: Auxiliar de Bodega, Analista de Calidad…

    **Cargo no es lo mismo que rol del sistema**, aunque el modelo anterior
    los mezclaba en una sola tabla `roldb`. El cargo describe qué hace una
    persona y por lo tanto **es contenido consultable**, mantenido por el
    jefe de área. El rol (Admin / Jefe de Área / Trabajador) solo dice qué
    botones se ven, y vive en los grupos nativos de Django.

    De aquí sale la inducción sin construir un LMS: si el cargo tiene sus
    términos y sus documentos enganchados, y cada persona tiene su cargo, el
    sistema ya sabe qué debe leer alguien el día que entra. La ruta no se
    programa — **emerge**.
    """

    nombre = models.CharField(max_length=150, verbose_name="Nombre del cargo")
    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name="cargos",
        verbose_name="Área",
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    funciones = models.TextField(
        blank=True,
        verbose_name="Funciones y responsabilidades",
    )
    reporta_a = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinados",
        verbose_name="Reporta a",
    )
    terminos = models.ManyToManyField(
        "contenido.Termino",
        blank=True,
        related_name="cargos",
        verbose_name="Términos que debe conocer",
    )
    documentos = models.ManyToManyField(
        "contenido.Documento",
        blank=True,
        related_name="cargos",
        verbose_name="Documentos que debe leer",
    )

    objects = CargoQuerySet.as_manager()

    class Meta:
        db_table = "cargo"
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ["area__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["nombre", "area"],
                name="cargo_unico_por_area",
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"


class Termino(ContenidoPublicable):
    """
    La unidad mínima de conocimiento: una palabra y qué significa *aquí*.

    ── Las dos capas ────────────────────────────────────────────────────
    Cada término tiene una **definición** corta y un **detalle** extenso.
    La definición se puede marcar pública, y entonces la ve toda la empresa;
    el detalle es siempre de las áreas dueñas. Eso resuelve tres problemas
    de un solo golpe:

    - El contenido transversal: un término sin áreas dueñas es de todos.
    - El aislamiento por área: el detalle no sale del pasillo.
    - Que nadie quede sin saber a quién preguntar (P4): quien no tiene
      acceso ve *que existe* y a quién pedírselo.

    ── Por qué `areas` es muchos-a-muchos y puede quedar vacío ───────────
    - Vacío  → transversal. Reglamento interno, organigrama.
    - Una    → propio de un área.
    - Varias → mismo significado compartido por dos áreas, una sola
               definición mantenida entre ambas.

    ── Por qué NO hay unicidad global sobre `nombre` ─────────────────────
    A propósito. "Corte" en Producción no es "Corte" en Contabilidad, y las
    dos definiciones tienen que convivir. El buscador devuelve las dos
    fichas, y eso no es un defecto: **le está enseñando al recién llegado
    que esa palabra es ambigua en su propia empresa**, que es justo lo que
    hoy nadie le dice y lo que le hace meter la pata la primera semana.
    """

    nombre = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name="Término",
    )
    definicion = models.TextField(
        verbose_name="Definición",
        help_text="Una o dos frases. Es lo que se lee primero.",
    )
    definicion_es_publica = models.BooleanField(
        default=True,
        verbose_name="Definición visible para toda la empresa",
        help_text=(
            "Si se desmarca, ni el resumen sale del área. Úsalo solo cuando la "
            "existencia misma del concepto sea sensible."
        ),
    )
    detalle = models.TextField(
        blank=True,
        verbose_name="Detalle (restringido al área)",
        help_text="Cómo se calcula, con qué formato, en qué procedimiento aparece.",
    )
    ejemplo = models.TextField(
        blank=True,
        verbose_name="Ejemplo de uso",
        help_text="Una frase real donde se use el término.",
    )
    areas = models.ManyToManyField(
        Area,
        blank=True,
        related_name="terminos",
        verbose_name="Áreas dueñas",
        help_text="Vacío = transversal, lo ve toda la empresa.",
    )

    objects = ContenidoQuerySet.as_manager()

    @staticmethod
    def filtro_ajeno_visible():
        """
        Un término de otra área aparece **solo si su definición es pública**.

        Si el jefe marcó la definición como no pública, el término es
        invisible del todo para el resto: ni se sabe que existe. Es la
        excepción deliberada a P4, para los casos en que hasta el nombre del
        concepto sea sensible.
        """
        return models.Q(definicion_es_publica=True)

    class Meta:
        db_table = "termino"
        verbose_name = "Término"
        verbose_name_plural = "Términos"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre", "estado"], name="termino_nombre_estado_idx"),
        ]

    def __str__(self):
        return self.nombre

    @property
    def es_transversal(self) -> bool:
        """Sin áreas dueñas: pertenece a toda la empresa."""
        return not self.areas.exists()

    def puede_ver_detalle(self, usuario) -> bool:
        """
        ¿Este usuario tiene derecho a la **capa restringida**?

        Ojo con la diferencia: `visibles_para` decide si el término aparece
        en la lista; esto decide si además se le enseña el detalle. Un
        término puede ser visible y estar bloqueado a la vez — es
        exactamente el caso del candado (P4).
        """
        if es_admin(usuario):
            return True
        if self.es_transversal:
            return True
        mis_areas = ids_areas_del_usuario(usuario)
        return bool(mis_areas & set(self.areas.values_list("id", flat=True)))

    def encargado(self):
        """
        A quién pedirle acceso. Es lo que impide el callejón sin salida (P4).

        Devuelve el jefe de la primera área dueña que tenga uno. Sin esto, el
        usuario bloqueado vuelve a preguntarle a gente al azar, que es
        justamente lo que el sistema vino a evitar.
        """
        for area in self.areas.select_related("jefe").all():
            if area.jefe_id:
                return area.jefe
        return None


class Sinonimo(ModeloBase):
    """
    Las otras formas de nombrar lo mismo.

    Es tabla aparte y no una lista dentro del término porque el buscador
    tiene que poder indexarlos y encontrarlos uno a uno.

    **Ninguna tecnología adivina esto.** Que en esta empresa a la carretilla
    le digan "la 47" no lo deduce ni el mejor modelo del mundo: lo escribe
    una persona que trabaja ahí. Es el campo más barato de llenar y el que
    más búsquedas fallidas evita.
    """

    termino = models.ForeignKey(
        Termino,
        on_delete=models.CASCADE,
        related_name="sinonimos",
        verbose_name="Término",
    )
    texto = models.CharField(max_length=200, db_index=True, verbose_name="Sinónimo")

    class Meta:
        db_table = "sinonimo"
        verbose_name = "Sinónimo"
        verbose_name_plural = "Sinónimos"
        ordering = ["texto"]
        constraints = [
            models.UniqueConstraint(
                fields=["termino", "texto"],
                name="sinonimo_unico_por_termino",
            )
        ]

    def __str__(self):
        return f"{self.texto} → {self.termino.nombre}"


class Documento(ContenidoPublicable):
    """
    La evidencia: el PDF, el manual, la foto del procedimiento.

    Diferencias con el `repodb` anterior:

    - **El archivo es obligatorio.** Antes era opcional en la tabla cuya
      razón de ser era guardar un archivo, así que se podían crear
      documentos sin documento.
    - **Puede ser transversal**, igual que un término (sin áreas dueñas).
    - **Guarda el texto extraído**, que es lo que permite buscar *dentro*
      del contenido y no solo por el título.
    - **Se reemplaza sin perder el anterior** (P7): la versión vieja queda
      archivada y recuperable, pero desaparece de las búsquedas. Es un
      "deshacer", no un árbol de treinta versiones (F-NO-10).

    El binario va al disco y a la base solo su registro (P9). Guardar
    archivos en la base hincha los backups hasta lo ingobernable y llena la
    memoria del servidor con un solo video.
    """

    archivo = models.FileField(
        upload_to="documentos/%Y/%m/",
        verbose_name="Archivo",
        validators=[validar_archivo],
    )
    nombre = models.CharField(max_length=255, db_index=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    areas = models.ManyToManyField(
        Area,
        blank=True,
        related_name="documentos",
        verbose_name="Áreas dueñas",
        help_text="Vacío = transversal, lo ve toda la empresa.",
    )
    tipo_mime = models.CharField(max_length=120, blank=True, verbose_name="Tipo de archivo")
    tamano_bytes = models.PositiveBigIntegerField(default=0, verbose_name="Tamaño")
    texto_extraido = models.TextField(
        blank=True,
        verbose_name="Texto extraído",
        help_text="Lo que se pudo leer del archivo. Alimenta la búsqueda dentro del contenido.",
    )
    texto_por_ocr = models.BooleanField(
        default=False,
        verbose_name="El texto se obtuvo por OCR",
        help_text=(
            "El OCR se equivoca. Marcarlo permite avisar de que el texto puede "
            "no ser fiel y llevar siempre al original (P6)."
        ),
    )
    reemplaza_a = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reemplazado_por",
        verbose_name="Reemplaza a",
    )
    enlace_externo = models.URLField(
        blank=True,
        verbose_name="Enlace externo",
        help_text="Para video, que se enlaza y no se aloja.",
    )

    objects = ContenidoQuerySet.as_manager()

    @staticmethod
    def filtro_ajeno_visible():
        """
        Un documento de otra área **sí se ve en las listas**: su nombre, su
        área y quién lo custodia. Lo que no se puede es abrirlo.

        Es la metáfora de la biblioteca que eligió el autor: ves los pasillos
        cerrados y sabes a quién pedirle la llave, en vez de creer que el
        pasillo no existe (P4).

        ⚠️ `pk__isnull=False` y no `Q()` a secas. Un `Q()` vacío **no
        significa "siempre verdadero"**: significa "sin condición", y al
        combinarlo con `|` Django simplemente lo descarta. El resultado era
        que los documentos ajenos desaparecían en vez de aparecer con
        candado. Lo cazó la prueba `test_el_archivo_de_otra_area_no_viaja`.
        """
        return models.Q(pk__isnull=False)

    class Meta:
        db_table = "documento"
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-creado_en"]

    def __str__(self):
        return self.nombre

    @property
    def es_transversal(self) -> bool:
        return not self.areas.exists()

    def puede_ver_detalle(self, usuario) -> bool:
        """
        Para un documento, "ver el detalle" es **poder descargarlo**.

        A diferencia del término, un documento no tiene capa pública: o se
        tiene acceso al archivo o no. Lo que sí se muestra siempre es que
        existe y de quién es, para no dejar a nadie sin saber a quién pedir.
        """
        if es_admin(usuario):
            return True
        if self.es_transversal:
            return True
        mis_areas = ids_areas_del_usuario(usuario)
        return bool(mis_areas & set(self.areas.values_list("id", flat=True)))

    def encargado(self):
        for area in self.areas.select_related("jefe").all():
            if area.jefe_id:
                return area.jefe
        return None

    def archivar_y_reemplazar(self, nuevo: "Documento", usuario=None):
        """
        Pone el documento nuevo en el sitio del viejo, sin perder el viejo.

        El anterior queda ARCHIVADO: recuperable si hace falta, invisible el
        99 % del tiempo. Nada se borra en silencio (P7).
        """
        nuevo.reemplaza_a = self
        nuevo.actualizado_por = usuario
        nuevo.save()
        self.estado = EstadoContenido.ARCHIVADO
        self.actualizado_por = usuario
        self.save(update_fields=["estado", "actualizado_por", "actualizado_en"])
        return nuevo


class MencionEnDocumento(ModeloBase):
    """
    Dónde aparece un término dentro de un documento, con su fragmento.

    Esto es P3 (trazabilidad) hecho dato: la ficha del término puede mostrar
    *"aparece en el Procedimiento de Bodega, página 4"* con la frase exacta.
    Sin esto, una definición es la palabra de alguien; con esto, es
    verificable contra la fuente.
    """

    termino = models.ForeignKey(
        Termino,
        on_delete=models.CASCADE,
        related_name="menciones",
        verbose_name="Término",
    )
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name="menciones",
        verbose_name="Documento",
    )
    fragmento = models.TextField(
        blank=True,
        verbose_name="Fragmento citado",
        help_text="Copiado literal del documento. No se parafrasea (P6).",
    )
    ubicacion = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Ubicación",
        help_text="Página, sección o apartado.",
    )

    class Meta:
        db_table = "mencion_en_documento"
        verbose_name = "Mención en documento"
        verbose_name_plural = "Menciones en documentos"
        constraints = [
            models.UniqueConstraint(
                fields=["termino", "documento", "ubicacion"],
                name="mencion_unica",
            )
        ]

    def __str__(self):
        return f"{self.termino.nombre} en {self.documento.nombre}"
