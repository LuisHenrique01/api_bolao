from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from usuario.api.serializers import CriarUsuarioSerializer

from usuario.models import Usuario

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
        serializer = CriarUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = serializer.data
        response.update(self.get_token(self.get_user(response)))
        return Response(response, status=status.HTTP_201_CREATED)
