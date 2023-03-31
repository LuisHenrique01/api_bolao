from rest_framework import routers
from .api.viewsets import CriarUsuarioViewSet, UsuarioViewSet, CarteiraViewSet, HistoricoTransfereciaViewSet


usuarioRouters = routers.DefaultRouter()
usuarioRouters.register('', UsuarioViewSet)
usuarioRouters.register('criar', CriarUsuarioViewSet)
usuarioRouters.register('carteira', CarteiraViewSet)
usuarioRouters.register('carteira/historico', HistoricoTransfereciaViewSet)
