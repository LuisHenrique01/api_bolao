from rest_framework import routers
from .api.viewsets import CriarUsuarioViewSet


usuarioRouters = routers.DefaultRouter()
usuarioRouters.register('criar', CriarUsuarioViewSet)