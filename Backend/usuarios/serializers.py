"""Serializers de identidad y estructura."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from comun.permisos import Rol, area_a_cargo, es_admin, es_jefe_de_area
from .models import Area, TipoIdentificacion, Usuario, UsuarioArea


class TipoIdentificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoIdentificacion
        fields = ["id", "nombre", "abreviatura"]


class AreaSerializer(serializers.ModelSerializer):
    jefe_nombre = serializers.CharField(source="jefe.get_full_name", read_only=True, default="")
    total_miembros = serializers.IntegerField(source="miembros.count", read_only=True)

    class Meta:
        model = Area
        fields = ["id", "nombre", "descripcion", "activa", "jefe", "jefe_nombre", "total_miembros"]
        # `jefe` solo lo cambia un administrador. Se blinda en la vista, no
        # aquí: un serializer no ve quién hace la petición hasta que se le
        # pasa el contexto, y confiar en eso es frágil.


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Nunca expone `fields = '__all__'`, y es deliberado.

    Con `__all__`, cualquier campo que se añada al modelo en el futuro sale
    publicado por la API sin que nadie lo decida. En un modelo con datos
    personales eso es una fuga esperando su turno. Aquí los campos se
    enumeran: lo que no está escrito, no sale.
    """

    nombre_completo = serializers.CharField(source="get_full_name", read_only=True)
    identificacion = serializers.CharField(read_only=True)
    tipo_identificacion_nombre = serializers.CharField(
        source="tipo_identificacion.abreviatura", read_only=True, default=""
    )
    cargo_nombre = serializers.CharField(source="cargo.nombre", read_only=True, default="")
    areas = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    area_a_cargo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "first_name", "last_name", "nombre_completo", "email",
            "tipo_identificacion", "tipo_identificacion_nombre",
            "numero_identificacion", "identificacion", "telefono",
            "cargo", "cargo_nombre", "areas", "roles", "area_a_cargo",
            "is_active", "debe_cambiar_password", "last_login",
        ]
        read_only_fields = ["last_login", "debe_cambiar_password"]

    def get_areas(self, obj):
        return [
            {"id": ua.area_id, "nombre": ua.area.nombre}
            for ua in obj.areas_asignadas.select_related("area")
        ]

    def get_roles(self, obj):
        return list(obj.groups.values_list("name", flat=True))

    def get_area_a_cargo(self, obj):
        a = getattr(obj, "area_a_cargo", None)
        return {"id": a.id, "nombre": a.nombre} if a else None


class CrearUsuarioSerializer(serializers.ModelSerializer):
    """
    Alta de personal. Nadie se registra solo: siempre lo da de alta alguien.

    La contraseña se entrega en mano, así que `debe_cambiar_password` queda
    en `True` y el sistema la exige cambiar en el primer ingreso — quien la
    entregó también la conoce.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    areas = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Area.objects.all(), required=False, write_only=True
    )
    rol = serializers.ChoiceField(choices=Rol.TODOS, default=Rol.TRABAJADOR, write_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "password", "first_name", "last_name", "email",
            "tipo_identificacion", "numero_identificacion", "telefono",
            "cargo", "areas", "rol",
        ]

    def validate_password(self, valor):
        try:
            validate_password(valor)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return valor

    def validate(self, datos):
        """
        Aquí se para la escalada de privilegios.

        Un jefe de área podría, llamando a la API directamente, intentar
        crear a alguien como Administrador o meterlo en un área que no es la
        suya. Las dos cosas se rechazan. No basta con ocultar las opciones en
        la interfaz: la interfaz no es una barrera de seguridad.
        """
        quien = self.context["request"].user
        if es_admin(quien):
            return datos

        if datos.get("rol") in (Rol.ADMIN, Rol.JEFE_AREA):
            raise serializers.ValidationError(
                {"rol": "Solo un administrador puede crear administradores o jefes de área."}
            )

        propia = area_a_cargo(quien)
        if not propia:
            raise serializers.ValidationError("No diriges ningún área.")

        pedidas = datos.get("areas") or []
        ajenas = [a.nombre for a in pedidas if a.id != propia.id]
        if ajenas:
            raise serializers.ValidationError(
                {"areas": f"Solo puedes dar de alta gente en «{propia.nombre}». Ajenas: {', '.join(ajenas)}."}
            )
        if not pedidas:
            datos["areas"] = [propia]
        return datos

    def create(self, datos):
        from django.contrib.auth.models import Group

        areas = datos.pop("areas", [])
        rol = datos.pop("rol", Rol.TRABAJADOR)
        password = datos.pop("password")

        usuario = Usuario(**datos)
        usuario.set_password(password)
        usuario.debe_cambiar_password = True
        usuario.is_staff = rol in (Rol.ADMIN, Rol.JEFE_AREA)   # acceso al panel
        usuario.save()

        grupo = Group.objects.filter(name=rol).first()
        if grupo:
            usuario.groups.add(grupo)
        for area in areas:
            UsuarioArea.objects.get_or_create(usuario=usuario, area=area, defaults={"creado_por": self.context["request"].user})
        return usuario


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(write_only=True, min_length=8)

    def validate_password_nueva(self, valor):
        try:
            validate_password(valor, self.context["request"].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return valor

    def validate_password_actual(self, valor):
        if not self.context["request"].user.check_password(valor):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return valor

    def validate(self, datos):
        if datos["password_actual"] == datos["password_nueva"]:
            raise serializers.ValidationError(
                {"password_nueva": "La contraseña nueva tiene que ser distinta de la actual."}
            )
        return datos
