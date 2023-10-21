from rest_framework.viewsets import ViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from core import STATUS_HISTORICO
from core.permissions import CARTEIRA_PERMISSIONS
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import PermissionDenied

from core.custom_exception import (SaldoInvalidoException, UsuarioNaoEncontrado, DepositoInvalidoException,
                                   UnavailableService)
from core.models import HistoricoTransacao
from usuario.api.serializers import (CriarUsuarioSerializer, UsuarioNotificacaoSerializer, UsuarioNovaSenhaSerializer,
                                     UsuarioSerializer, CarteiraSerializer, HistoricoTransacaoSerializer,
                                     AsaasInfosSerializer)

from usuario.models import Carteira, CodigosDeValidacao, Usuario


class CriarUsuarioViewSet(ViewSet):

    queryset = Usuario.objects.all()
    permission_classes = [AllowAny]

    def is_authenticated(self, request):
        return bool(request.user and request.user.is_authenticated)

    def get_user(self, data):
        return Usuario.objects.get(email=data['email'])

    def get_token(responseself, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

    def create(self, request, *args, **kwargs):
        serializer = CriarUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = serializer.data
        response.update(self.get_token(self.get_user(response)))
        return Response(response, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'], url_path='codigo-recuperacao-senha')
    def codigo_recuperacao_senha(self, request):
        try:
            serializer = UsuarioNotificacaoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.recuperar_senha()
            return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
        except UsuarioNaoEncontrado as e:
            return Response(e.serializer, status=status.HTTP_404_NOT_FOUND)
        except NotImplementedError as e:
            return Response({'message': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=False, methods=['POST'], url_path='confirmar-codigo')
    def confirmar_codigo(self, request):
        if CodigosDeValidacao.valido(request.data['codigo']):
            codigo = CodigosDeValidacao.objects.get(codigo=request.data['codigo'])
            codigo.confirmado = True
            if self.is_authenticated(request):
                if codigo.tipo == 'email':
                    codigo.permissao.email_verificado = True
                if codigo.tipo == 'sms':
                    codigo.permissao.sms_verificado = True
                codigo.permissao.save()
            codigo.save()
            return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
        return Response({'message': 'Código inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], url_path='recuperar-senha')
    def recuperar_senha(self, request):
        try:
            serializer = UsuarioNovaSenhaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.mudar_senha()
            return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
        except PermissionDenied:
            return Response({'message': 'Senha atual inválida'}, status=status.HTTP_401_UNAUTHORIZED)
        except UsuarioNaoEncontrado as e:
            return Response(e.serializer, status=status.HTTP_404_NOT_FOUND)


class UsuarioViewSet(ViewSet):

    queryset = Usuario.objects.all()

    def list(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['PATCH'], url_path='editar')
    def editar(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], url_path='mudar-senha')
    def mudar_senha(self, request):
        try:
            serializer = UsuarioNovaSenhaSerializer(data={**request.data, 'id': request.user.id})
            serializer.is_valid(raise_exception=True)
            serializer.mudar_senha()
            return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
        except PermissionDenied:
            return Response({'message': 'Senha atual inválida'}, status=status.HTTP_401_UNAUTHORIZED)
        except UsuarioNaoEncontrado as e:
            return Response(e.serializer, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['POST'], url_path='validar-usuario')
    def codigo_validar_usuario(self, request):
        try:
            forma = request.data['forma']
            serializer = UsuarioNotificacaoSerializer(data={forma: getattr(request.user, forma)})
            serializer.is_valid(raise_exception=True)
            serializer.validar_usuario()
            return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
        except UsuarioNaoEncontrado as e:
            return Response(e.serializer, status=status.HTTP_404_NOT_FOUND)
        except NotImplementedError as e:
            return Response({'message': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)


class CarteiraViewSet(ViewSet):

    queryset = Carteira.objects.all()
    permission_classes = CARTEIRA_PERMISSIONS

    def list(self, request):
        serializer = CarteiraSerializer(request.user.carteira)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], url_path='depositar')
    def depositar(self, request):
        try:
            serializer = CarteiraSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            transaction = serializer.depositar(request.user.carteira)
            pix = AsaasInfosSerializer(transaction.asaas_infos)
            return Response(pix.data, status=status.HTTP_200_OK)
        except DepositoInvalidoException as e:
            return Response(e.serializer, status=status.HTTP_406_NOT_ACCEPTABLE)
        except UnavailableService as e:
            return Response(e.serializer, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except NotImplementedError as e:
            return Response({'message': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=False, methods=['POST'], url_path='sacar')
    def sacar(self, request):
        try:
            serializer = CarteiraSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            qr_code = serializer.sacar(request.user.carteira)
            return Response(qr_code, status=status.HTTP_200_OK)
        except SaldoInvalidoException as e:
            return Response(e.serializer, status=status.HTTP_406_NOT_ACCEPTABLE)
        except NotImplementedError as e:
            return Response({'message': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)


class HistoricoTransfereciaViewSet(ReadOnlyModelViewSet):
    queryset = HistoricoTransacao.objects.filter(status=STATUS_HISTORICO['CONFIRMED'])
    serializer_class = HistoricoTransacaoSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(carteira=self.request.user.carteira).order_by('-created_at')
        return queryset
