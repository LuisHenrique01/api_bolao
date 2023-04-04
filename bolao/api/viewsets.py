from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from bolao.api.serializers import (BolaoSerializer, CampeonatoSerializer, JogoSerializer,
                                   TimeSerializer, CriarBolaoSerializer)
from bolao.models import Campeonato, Jogo, Time, Bolao
from core.permissions import LEITURA_OU_AUTENTICACAO_COMPLETA
from bolao import STATUS_BOLAO


class CampeonatoViewSet(ReadOnlyModelViewSet):
    queryset = Campeonato.objects.filter(ativo=True)
    serializer_class = CampeonatoSerializer
    permission_classes = LEITURA_OU_AUTENTICACAO_COMPLETA


class TimeViewSet(ReadOnlyModelViewSet):
    queryset = Time.objects.all()
    serializer_class = TimeSerializer
    permission_classes = LEITURA_OU_AUTENTICACAO_COMPLETA


class JogoViewSet(ReadOnlyModelViewSet):
    queryset = Jogo.objects.all()
    serializer_class = JogoSerializer
    permission_classes = LEITURA_OU_AUTENTICACAO_COMPLETA


class BolaoViewSet(ViewSet):

    queryset = Bolao.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(status=STATUS_BOLAO['ATIVO'])
        serializer = BolaoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = CriarBolaoSerializer(data={**request.data, 'criador': request.user.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        bolao = get_object_or_404(self.queryset, pk=pk)
        serializer = BolaoSerializer(bolao)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], url_path='meus-boloes')
    def meus_boloes(self, request):
        queryset = self.queryset.filter(criador=request.user)
        serializer = BolaoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
