from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RolViewSet, TipoIdViewSet, PerfilViewSet, AreaViewSet, UserAreaViewSet, UserRolViewSet, TrabajadorViewSet, RepoViewSet, EvaluacionViewSet

router = DefaultRouter()
router.register(r'roles', RolViewSet)
router.register(r'tipos-id', TipoIdViewSet)
router.register(r'perfiles', PerfilViewSet)
router.register(r'areas', AreaViewSet)
router.register(r'userarea', UserAreaViewSet)
router.register(r'userrol', UserRolViewSet)
router.register(r'trabajadores', TrabajadorViewSet)
router.register(r'repo', RepoViewSet)
router.register(r'evaluaciones', EvaluacionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]