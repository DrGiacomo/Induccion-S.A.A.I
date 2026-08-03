"""
Serializers del contenido.

Aquí vive **la segunda mitad de los permisos**. La primera —qué aparece en
la lista— la resuelve `ContenidoQuerySet.visibles_para()`. Esta decide, de
lo que sí aparece, **cuánto se enseña**.

Son dos cosas distintas y las dos hacen falta. Un término puede ser visible
y estar bloqueado a la vez: eso es exactamente el candado de P4.
"""

from rest_framework import serializers

from comun.permisos import es_admin
from usuarios.models import Area

from .models import Cargo, Documento, MencionEnDocumento, Sinonimo, Termino


class SinonimoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sinonimo
        fields = ["id", "texto"]


class AreaMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "nombre"]


class MencionSerializer(serializers.ModelSerializer):
    documento_nombre = serializers.CharField(source="documento.nombre", read_only=True)

    class Meta:
        model = MencionEnDocumento
        fields = ["id", "documento", "documento_nombre", "fragmento", "ubicacion"]


class TerminoSerializer(serializers.ModelSerializer):
    """
    La ficha de un término, recortada según quién pregunte.

    ⚠️ **Los campos restringidos no se ocultan: se quitan de la respuesta.**
    Mandarlos y esconderlos en la interfaz no sirve de nada — el dato ya
    viajó y cualquiera lo ve abriendo las herramientas del navegador. Si no
    corresponde, no sale del servidor.
    """

    areas_detalle = AreaMiniSerializer(source="areas", many=True, read_only=True)
    sinonimos = SinonimoSerializer(many=True, read_only=True)
    menciones = MencionSerializer(many=True, read_only=True)
    es_transversal = serializers.BooleanField(read_only=True)
    creado_por_nombre = serializers.CharField(
        source="creado_por.get_full_name", read_only=True, default=""
    )

    # Los tres campos del candado (P4)
    acceso_restringido = serializers.SerializerMethodField()
    encargado = serializers.SerializerMethodField()

    class Meta:
        model = Termino
        fields = [
            "id", "nombre", "definicion", "definicion_es_publica", "detalle", "ejemplo",
            "areas", "areas_detalle", "es_transversal", "sinonimos", "menciones",
            "estado", "creado_en", "actualizado_en", "creado_por_nombre",
            "acceso_restringido", "encargado",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]

    # ── El recorte ──────────────────────────────────────────────────────

    def _usuario(self):
        peticion = self.context.get("request")
        return getattr(peticion, "user", None)

    def get_acceso_restringido(self, obj) -> bool:
        return not obj.puede_ver_detalle(self._usuario())

    def get_encargado(self, obj):
        """
        A quién pedirle acceso. **Solo se calcula si hace falta.**

        Es P4 hecho dato: sin esto el usuario bloqueado vuelve a preguntarle
        a gente al azar, que es justo lo que el sistema vino a evitar.
        """
        if obj.puede_ver_detalle(self._usuario()):
            return None
        jefe = obj.encargado()
        areas = list(obj.areas.values_list("nombre", flat=True))
        return {
            "nombre": jefe.get_full_name() if jefe else None,
            "email": jefe.email if jefe else None,
            "areas": areas,
            "mensaje": (
                f"El detalle de este término pertenece a {' y '.join(areas)}. "
                + (f"Habla con {jefe.get_full_name()} para pedir acceso."
                   if jefe else "Todavía no hay un jefe asignado a esa área.")
            ),
        }

    def to_representation(self, instancia):
        datos = super().to_representation(instancia)
        usuario = self._usuario()

        if instancia.puede_ver_detalle(usuario):
            return datos

        # Capa restringida fuera. No se vacía el campo: se elimina la clave,
        # para que ni siquiera se sepa cuánto había escrito.
        for campo in ("detalle", "ejemplo", "menciones"):
            datos.pop(campo, None)

        # Si además la definición no es pública, no debería haber llegado
        # aquí (el queryset ya lo filtró). Cinturón y tirantes: si por
        # cualquier ruta futura se colara, tampoco se enseña.
        if not instancia.definicion_es_publica:
            datos["definicion"] = ""

        return datos

    # ── Escritura ───────────────────────────────────────────────────────

    def validate(self, datos):
        """
        Un jefe de área no puede crear contenido en un área ajena, ni marcarlo
        como transversal — lo transversal es de todos y solo el administrador
        decide sobre ello.
        """
        from comun.permisos import area_a_cargo

        usuario = self._usuario()
        if es_admin(usuario):
            return datos

        propia = area_a_cargo(usuario)
        if not propia:
            raise serializers.ValidationError("No diriges ningún área.")

        areas = datos.get("areas")
        if areas is None and self.instance is not None:
            return datos
        if not areas:
            raise serializers.ValidationError(
                {"areas": "Un jefe de área no puede crear contenido transversal. Eso lo decide el administrador."}
            )
        ajenas = [a.nombre for a in areas if a.id != propia.id]
        if ajenas:
            raise serializers.ValidationError(
                {"areas": f"Solo puedes crear contenido en «{propia.nombre}». Ajenas: {', '.join(ajenas)}."}
            )
        return datos


class TerminoListaSerializer(TerminoSerializer):
    """
    Versión ligera para listados y resultados de búsqueda.

    Se separa por rendimiento, no por permisos: la ficha completa arrastra
    sinónimos y menciones, y pedir eso para cincuenta resultados son
    cincuenta consultas extra. Con el objetivo de <500 ms del §8, eso importa.
    """

    class Meta(TerminoSerializer.Meta):
        fields = [
            "id", "nombre", "definicion", "areas_detalle", "es_transversal",
            "estado", "acceso_restringido", "encargado",
        ]


class DocumentoSerializer(serializers.ModelSerializer):
    areas_detalle = AreaMiniSerializer(source="areas", many=True, read_only=True)
    es_transversal = serializers.BooleanField(read_only=True)
    acceso_restringido = serializers.SerializerMethodField()
    encargado = serializers.SerializerMethodField()
    creado_por_nombre = serializers.CharField(
        source="creado_por.get_full_name", read_only=True, default=""
    )
    tamano_legible = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = [
            "id", "nombre", "descripcion", "archivo", "enlace_externo",
            "areas", "areas_detalle", "es_transversal",
            "tipo_mime", "tamano_bytes", "tamano_legible", "texto_por_ocr",
            "estado", "creado_en", "actualizado_en", "creado_por_nombre",
            "acceso_restringido", "encargado",
        ]
        read_only_fields = ["tipo_mime", "tamano_bytes", "creado_en", "actualizado_en"]

    def _usuario(self):
        return getattr(self.context.get("request"), "user", None)

    def get_acceso_restringido(self, obj) -> bool:
        return not obj.puede_ver_detalle(self._usuario())

    def get_encargado(self, obj):
        if obj.puede_ver_detalle(self._usuario()):
            return None
        jefe = obj.encargado()
        areas = list(obj.areas.values_list("nombre", flat=True))
        return {
            "nombre": jefe.get_full_name() if jefe else None,
            "email": jefe.email if jefe else None,
            "areas": areas,
            "mensaje": (
                f"Este documento pertenece a {' y '.join(areas)}. "
                + (f"Habla con {jefe.get_full_name()} para pedir acceso."
                   if jefe else "Todavía no hay un jefe asignado a esa área.")
            ),
        }

    def get_tamano_legible(self, obj):
        n = obj.tamano_bytes or 0
        for unidad in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.0f} {unidad}" if unidad == "B" else f"{n:.1f} {unidad}"
            n /= 1024
        return f"{n:.1f} TB"

    def to_representation(self, instancia):
        datos = super().to_representation(instancia)
        if not instancia.puede_ver_detalle(self._usuario()):
            # **La URL del archivo se quita.** Un documento de otra área se
            # ve —existe, es de tal área, pregúntale a tal persona— pero no
            # se descarga. Dejar la URL y esconder el botón sería regalar el
            # archivo a quien mire la respuesta.
            datos["archivo"] = None
            datos["enlace_externo"] = ""
        return datos

    def create(self, datos):
        archivo = datos.get("archivo")
        if archivo:
            datos["tamano_bytes"] = archivo.size
            datos["tipo_mime"] = getattr(archivo, "content_type", "") or ""
        return super().create(datos)


class CargoSerializer(serializers.ModelSerializer):
    area_nombre = serializers.CharField(source="area.nombre", read_only=True)
    reporta_a_nombre = serializers.CharField(source="reporta_a.nombre", read_only=True, default="")
    total_terminos = serializers.IntegerField(source="terminos.count", read_only=True)
    total_documentos = serializers.IntegerField(source="documentos.count", read_only=True)

    class Meta:
        model = Cargo
        fields = [
            "id", "nombre", "area", "area_nombre", "descripcion", "funciones",
            "reporta_a", "reporta_a_nombre", "terminos", "documentos",
            "total_terminos", "total_documentos", "estado", "creado_en",
        ]
        read_only_fields = ["creado_en"]
