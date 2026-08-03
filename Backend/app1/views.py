from rest_framework import viewsets
from .models import roldb, tipo_id_db, perfildb, areadb, userarea, userrol, trabajadordb, repodb, evaluaciondb
from .serializers import RolSerializer, TipoIdSerializer, PerfilSerializer, AreaSerializer, UserAreaSerializer, UserRolSerializer, TrabajadorSerializer, RepoSerializer, EvaluacionSerializer

class RolViewSet(viewsets.ModelViewSet):
    queryset = roldb.objects.all()
    serializer_class = RolSerializer

class TipoIdViewSet(viewsets.ModelViewSet):
    queryset = tipo_id_db.objects.all()
    serializer_class = TipoIdSerializer

class PerfilViewSet(viewsets.ModelViewSet):
    queryset = perfildb.objects.all()
    serializer_class = PerfilSerializer

class AreaViewSet(viewsets.ModelViewSet):
    queryset = areadb.objects.all()
    serializer_class = AreaSerializer

class UserAreaViewSet(viewsets.ModelViewSet):
    queryset = userarea.objects.all()
    serializer_class = UserAreaSerializer

class UserRolViewSet(viewsets.ModelViewSet):
    queryset = userrol.objects.all()
    serializer_class = UserRolSerializer

class TrabajadorViewSet(viewsets.ModelViewSet):
    queryset = trabajadordb.objects.all()
    serializer_class = TrabajadorSerializer

class RepoViewSet(viewsets.ModelViewSet):
    queryset = repodb.objects.all()
    serializer_class = RepoSerializer

class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = evaluaciondb.objects.all()
    serializer_class = EvaluacionSerializer