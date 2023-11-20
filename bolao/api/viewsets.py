from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from bolao.api.serializers import (PalpiteCriarSerializer, BilheteCriarSerializer, BilheteSerializer, BolaoSerializer,
                                   CampeonatoSerializer, JogoSerializer, TimeSerializer, CriarBolaoSerializer)
from bolao.filters import BolaoFilter
from bolao.mixins import ListCreateDetailOnlyMixin
from bolao.models import Bilhete, Campeonato, Jogo, Time, Bolao
from core.custom_exception import SaldoInvalidoException
from core.permissions import LEITURA_OU_AUTENTICACAO_COMPLETA
from bolao import STATUS_BOLAO


class CampeonatoViewSet(ReadOnlyModelViewSet):
    queryset = Campeonato.objects.filter(ativo=True)
    serializer_class = CampeonatoSerializer
    permission_classes = LEITURA_OU_AUTENTICACAO_COMPLETA
    search_fields = ['nome', 'pais', 'tipo']
    ordering_fields = ['nome']


class TimeViewSet(ReadOnlyModelViewSet):
    queryset = Time.objects.all()
    serializer_class = TimeSerializer
    permission_classes = LEITURA_OU_AUTENTICACAO_COMPLETA
    search_fields = ['nome']
    ordering_fields = ['nome']


class JogoViewSet(ReadOnlyModelViewSet):
    queryset = Jogo.objects.all()
    serializer_class = JogoSerializer
    permission_classes = LEITURA_OU_AUTENTICACAO_COMPLETA
    filterset_fields = ['data', 'status']
    search_fields = ['campeonato__nome', 'time_casa__nome', 'time_fora__nome']
    ordering_fields = ['data', 'status']


class BolaoViewSet(ModelViewSet):

    queryset = Bolao.objects.all()
    serializer_class = BolaoSerializer
    filterset_class = BolaoFilter
    search_fields = ['codigo', 'jogos__time_casa__nome', 'jogos__time_fora__nome']
    ordering_fields = ['estorno', 'taxa_banca', 'taxa_criador', 'taxa_criador', 'status', 'bilhetes_minimos']

    def get_queryset(self):
        if self.action == 'list':
            if status := self.request.GET.get('status'):
                return self.queryset.filter(status=status)
            return self.queryset.filter(status=STATUS_BOLAO['ATIVO'])
        return super().get_queryset()

    def create(self, request):
        serializer = CriarBolaoSerializer(data={**request.data, 'criador': request.user.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        bolao = get_object_or_404(self.queryset, pk=pk)
        serializer = BolaoSerializer(bolao)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        bolao = get_object_or_404(self.queryset, pk=pk)
        if request.user == bolao.criador:
            if bolao.status_atualizado in (STATUS_BOLAO['ATIVO'], STATUS_BOLAO['PALPITES PAUSADOS']):
                bolao.cancelar_bolao()
                return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
            return Response({'message': 'O bolão não pode mais ser cancelado.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['GET'], url_path='meus-boloes')
    def meus_boloes(self, request):
        queryset = self.queryset.filter(criador=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BolaoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='pausar-palpites')
    def pausar_palpites(self, request, pk=None):
        bolao = get_object_or_404(self.queryset, pk=pk)
        if request.user == bolao.criador:
            bolao.status = STATUS_BOLAO['PALPITES PAUSADOS']
            bolao.save()
            return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
        return Response({'message': 'O usuário atual não pode pausar o bolão.'}, status=status.HTTP_400_BAD_REQUEST)


class BilheteViewSet(ListCreateDetailOnlyMixin, ModelViewSet):

    queryset = Bilhete.objects.all()
    serializer_class = BilheteSerializer

    def get_queryset(self):
        return self.queryset.filter(usuario=self.request.user)

    @transaction.atomic
    def create(self, request):
        try:
            bilhete_serializer = BilheteCriarSerializer(data={'bolao': request.data['bolao'],
                                                              'usuario': request.user.id})
            bilhete_serializer.is_valid(raise_exception=True)
            bilhete = bilhete_serializer.save()
            for palpite in request.data['palpites']:
                palpite['bilhete'] = bilhete.id
                palpite_seriaizer = PalpiteCriarSerializer(data=palpite)
                palpite_seriaizer.is_valid(raise_exception=True)
                palpite_seriaizer.save()
            return Response(bilhete_serializer.data, status=status.HTTP_200_OK)
        except SaldoInvalidoException as e:
            return Response(e.serialize, status=status.HTTP_402_PAYMENT_REQUIRED)
