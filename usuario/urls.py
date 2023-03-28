from rest_framework import routers
from .api.viewsets import CriarUsuarioViewSet, UsuarioViewSet


usuarioRouters = routers.DefaultRouter()
usuarioRouters.register('criar', CriarUsuarioViewSet)
usuarioRouters.register('', UsuarioViewSet)