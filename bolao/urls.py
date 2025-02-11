from rest_framework import routers
from .api.viewsets import BilheteViewSet, CampeonatoViewSet, TimeViewSet, JogoViewSet, BolaoViewSet


bolaoRouters = routers.DefaultRouter()
bolaoRouters.register('bolao', BolaoViewSet)
bolaoRouters.register('campeonato', CampeonatoViewSet)
bolaoRouters.register('time', TimeViewSet)
bolaoRouters.register('jogo', JogoViewSet)
bolaoRouters.register('bilhete', BilheteViewSet)
