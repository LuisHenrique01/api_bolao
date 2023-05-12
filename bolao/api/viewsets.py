from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from bolao.api.serializers import (PalpiteCriarSerializer, BilheteCriarSerializer, BilheteSerializer, BolaoSerializer,
                                   CampeonatoSerializer, JogoSerializer, TimeSerializer, CriarBolaoSerializer)
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


class BolaoViewSet(ViewSet):

    queryset = Bolao.objects.all()
    filterset_fields = ['criador', 'estorno', 'taxa_banca__gte', 'taxa_banca__lte', 'taxa_criador__gte',
                        'taxa_criador__lte', 'status']
    search_fields = ['codigo', 'jogos__nome']
    ordering_fields = ['estorno', 'taxa_banca', 'taxa_criador', 'taxa_criador', 'status', 'bilhetes_minimos']

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


class BilheteViewSet(ViewSet):

    queryset = Bilhete.objects.all()

    def list(self, request):
        queryset = self.queryset.filter(usuario=request.user)
        serializer = BilheteSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
