from rest_framework import routers
from .api.viewsets import CampeonatoViewSet, TimeViewSet, JogoViewSet, BolaoViewSet


bolaoRouters = routers.DefaultRouter()
bolaoRouters.register('', BolaoViewSet)
bolaoRouters.register('campeonato', CampeonatoViewSet)
bolaoRouters.register('time', TimeViewSet)
bolaoRouters.register('jogo', JogoViewSet)
