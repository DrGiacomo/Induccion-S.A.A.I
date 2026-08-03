from rest_framework import serializers
from .models import roldb, tipo_id_db, perfildb, areadb, userarea, userrol, trabajadordb, repodb, evaluaciondb
from django.contrib.auth.models import User

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = roldb
        fields = '__all__'

class TipoIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = tipo_id_db
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    username = serializers.CharField(required=False)

    def validate_username(self, value):
        return value

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'username': {'validators': []},
            # 'password': {'required': False, 'allow_blank': True}
        }

class PerfilSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = perfildb
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password = validated_data.pop('password', None)
        user = User.objects.create(**user_data)
        if password:
            user.set_password(password)
            user.save()
        perfil = perfildb.objects.create(user=user, **validated_data)
        return perfil

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        password = user_data.pop('password', None)
        
        for attr, value in user_data.items():
            if attr == 'username' and value == instance.user.username:
                continue
            setattr(instance.user, attr, value)
        
        if password:
            instance.user.set_password(password)
        
        instance.user.save()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = areadb
        fields = '__all__'

class UserAreaSerializer(serializers.ModelSerializer):
    perfil_nombre = serializers.CharField(source='id_user.user.username', read_only=True)
    area_nombre = serializers.CharField(source='id_area.nombre', read_only=True)
    class Meta:
        model = userarea
        fields = '__all__'

class UserRolSerializer(serializers.ModelSerializer):
    perfil_nombre = serializers.CharField(source='id_user.user.username', read_only=True)
    rol_nombre = serializers.CharField(source='id_rol.nombre_rol', read_only=True)
    class Meta:
        model = userrol
        fields = '__all__'

class TrabajadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = trabajadordb
        fields = '__all__'

class RepoSerializer(serializers.ModelSerializer):
    class Meta:
        model = repodb
        fields = '__all__'

class EvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = evaluaciondb
        fields = '__all__'