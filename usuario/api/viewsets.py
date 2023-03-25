from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import PermissionDenied

from core.custom_exception import UsuarioNaoEncontrado
from usuario.api.serializers import CriarUsuarioSerializer, UsuarioNotificacaoSerializer, UsuarioNovaSenhaSerializer

from usuario.models import CodigosDeValidacao, Usuario

class CriarUsuarioViewSet(ViewSet):

    queryset = Usuario.objects.all()
    permission_classes = [AllowAny]

    def get_user(self, data):
        return Usuario.objects.get(email=data['email'])

    def get_token(responseself, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

    def create(self, request, *args, **kwargs):
        try:
            serializer = CriarUsuarioSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response = serializer.data
            response.update(self.get_token(self.get_user(response)))
            return Response(response, status=status.HTTP_201_CREATED)
        except Exception:
            return Response({'message': 'Erro interno no servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def codigo_recuperacao_senha(self, request):
        try:
            serializer = UsuarioNotificacaoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.enviar_codigo()
        except UsuarioNaoEncontrado as e:
            return Response(e.serializer, status=status.HTTP_404_NOT_FOUND)
        except NotImplementedError as e:
            return Response({'message': str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception:
            return Response({'message': 'Erro interno no servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def confirmar_codigo(self, request):
        try:
            if CodigosDeValidacao.valido(request.data['codigo']):
                codigo = CodigosDeValidacao.objects.get(codigo=request.data['codigo'])
                codigo.confirmado = True
                codigo.save()
                return Response({'message': 'Sucesso!'}, status=status.HTTP_200_OK)
            return Response({'message': 'Código inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'message': 'Erro interno no servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
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
        except Exception:
            return Response({'message': 'Erro interno no servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)