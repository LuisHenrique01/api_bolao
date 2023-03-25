import os
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from usuario.models import Carteira, Endereco, PermissoesNotificacao, Usuario
from core.custom_exception import UsuarioNaoEncontrado


class EnderecoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Endereco
        fields = '__all__'


class PermissoesSerializer(serializers.ModelSerializer):

    class Meta:
        model = PermissoesNotificacao
        fields = '__all__'


class CarteiraSerializer(serializers.ModelSerializer):

    class Meta:
        model = Carteira
        fields = '__all__'


class CriarUsuarioSerializer(serializers.ModelSerializer):

    endereco = EnderecoSerializer()
    permissoes = PermissoesSerializer()
    carteira = CarteiraSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['email', 'cpf', 'nome', 'password', 'data_nascimento', 'telefone', 'endereco', 'permissoes', 'carteira']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        endereco_instancia = EnderecoSerializer(data=validated_data['endereco'])
        permissoes_instancia = PermissoesSerializer(data=validated_data['endereco'])
        endereco_instancia.is_valid(raise_exception=True)
        permissoes_instancia.is_valid(raise_exception=True)
        validated_data['endereco'] = endereco_instancia.save()
        validated_data['permissoes'] = permissoes_instancia.save()
        return super().create(validated_data)


class UsuarioNotificacaoSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    sms = serializers.CharField(required=False)

    def enviar_codigo(self):
        try:
            if self.validated_data["email"]:
                usuario = Usuario.objects.get(email=self.validated_data['email'])
                usuario.permissoes.enviar_validacao_email()
            if self.validated_data["sms"]:
                usuario = Usuario.objects.get(telefone=self.validated_data['sms'])
                usuario.permissoes.enviar_validacao_sms()
        except ObjectDoesNotExist:
            raise UsuarioNaoEncontrado()


class UsuarioNovaSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    codigo = serializers.CharField(required=False)
    senha_atual = serializers.CharField(required=False)
    nova_senha = serializers.CharField()

    def mudar_senha(self):
        try:
            if self.validated_data['email']:
                usuario = Usuario.objects.get(email=self.validated_data['email'])
                if usuario.check_password(self.validated_data['senha_atual']):
                    usuario.set_password(self.validated_data['nova_senha'])
                    return usuario.save()
                raise PermissionDenied()

            usuario = Usuario.objects.get(permissoes__codigos__codigo=self.validated_data['codigo'])
            usuario.set_password(self.validated_data['nova_senha'])
            return usuario.save()
        except ObjectDoesNotExist:
            raise UsuarioNaoEncontrado()

    def validate(self, attrs):
        if not attrs['codigo'] and not attrs['senha_atual']:
            raise serializers.ValidationError("Para mudar a senha você deve preencher com a senha atual.")
        if not attrs['codigo'] and not attrs['email']:
            raise serializers.ValidationError("Para mudar a senha você deve preencher com o seu email.")
        return super().validate(attrs)