import os
from decimal import Decimal
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from core.models import HistoricoTransacao

from usuario.models import Carteira, Endereco, PermissoesNotificacao, Usuario
from core.custom_exception import UsuarioNaoEncontrado
from core.utils import qual_tipo_chave_pix


class EnderecoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Endereco
        fields = '__all__'


class PermissoesSerializer(serializers.ModelSerializer):

    class Meta:
        model = PermissoesNotificacao
        fields = '__all__'


class CarteiraSerializer(serializers.ModelSerializer):

    valor = serializers.DecimalField(max_digits=9, decimal_places=2, required=False)
    pix = serializers.CharField(required=False)

    class Meta:
        model = Carteira
        fields = '__all__'
        readonly = ['saldo', 'bloqueado']

    def validate_valor(self, value):
        if 'pix' in self.initial_data:
            valor_minimo = Decimal(os.getenv('MIN_SAQUE'))
        else:
            valor_minimo = Decimal(os.getenv('MIN_DEPOSITO'))
        if value < valor_minimo:
            raise serializers.ValidationError('Valor abaixo do permitido.')
        return value

    def validate_pix(self, value):
        PIX_ACEITOS = ("e-mail", "CPF", "telefone", "aleatorio")
        if qual_tipo_chave_pix(value) not in PIX_ACEITOS:
            raise serializers.ValidationError(f'Chave PIX inválida, acitamos apenas as seguintes chaves {PIX_ACEITOS}!')
        return value

    def depositar(self, carteira: Carteira):
        qr_code = carteira.solicitar_cash_in(self.validated_data['valor'])
        return qr_code

    def sacar(self, carteira: Carteira):
        qr_code = carteira.solicitar_cash_out(self.validated_data['valor'])
        return qr_code


class CriarUsuarioSerializer(serializers.ModelSerializer):

    endereco = EnderecoSerializer()
    permissoes = PermissoesSerializer()
    carteira = CarteiraSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['email', 'cpf', 'nome', 'password', 'data_nascimento', 'telefone',
                  'endereco', 'permissoes', 'carteira']
        read_only = ['id']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        endereco_instancia = EnderecoSerializer(data=validated_data['endereco'])
        permissoes_instancia = PermissoesSerializer(data=validated_data['permissoes'])
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
            if self.validated_data.get("email"):
                usuario = Usuario.objects.get(email=self.validated_data['email'])
                usuario.permissoes.enviar_validacao_email()
            if self.validated_data.get("sms"):
                usuario = Usuario.objects.get(telefone=self.validated_data['sms'])
                usuario.permissoes.enviar_validacao_sms()
        except ObjectDoesNotExist:
            raise UsuarioNaoEncontrado()


class UsuarioSerializer(serializers.ModelSerializer):
    endereco = EnderecoSerializer()
    permissoes = PermissoesSerializer()
    carteira = CarteiraSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'cpf', 'nome', 'password', 'data_nascimento', 'telefone',
                  'endereco', 'permissoes', 'carteira']
        read_only = ['id', 'cpf', 'data_nascimento']
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, instance, validated_data):
        if endereco := validated_data.get('endereco'):
            endereco_instancia = EnderecoSerializer(data=endereco, partial=True)
            endereco_instancia.is_valid(raise_exception=True)
            validated_data['endereco'] = endereco_instancia.save()
        if permissoes := validated_data.get('permissoes'):
            permissoes_instancia = PermissoesSerializer(data=permissoes, partial=True)
            permissoes_instancia.is_valid(raise_exception=True)
            validated_data['permissoes'] = permissoes_instancia.save()
        return super().update(instance, validated_data)


class UsuarioNovaSenhaSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    usuario = UsuarioSerializer(required=False)
    codigo = serializers.CharField(required=False)
    senha_atual = serializers.CharField(required=False)
    nova_senha = serializers.CharField()

    def mudar_senha(self):
        try:
            if usuario := self.validated_data.get('id'):
                usuario = Usuario.objects.get(id=self.validated_data['id'])
                if usuario.check_password(self.validated_data.get('senha_atual')):
                    usuario.set_password(self.validated_data['nova_senha'])
                    return usuario.save()
                raise PermissionDenied()

            usuario = Usuario.objects.get(permissoes__codigos__codigo=self.validated_data['codigo'],
                                          permissoes__codigos__confirmado=True)
            usuario.set_password(self.validated_data['nova_senha'])
            return usuario.save()
        except ObjectDoesNotExist:
            raise UsuarioNaoEncontrado()

    def validate(self, attrs):
        if not attrs.get('codigo') and not attrs.get('senha_atual'):
            raise serializers.ValidationError("Para mudar a senha você deve preencher com a senha atual.")
        if not attrs.get('codigo') and not attrs.get('id'):
            raise serializers.ValidationError("Para mudar a senha você deve preencher com o seu email.")
        return super().validate(attrs)


class HistoricoTransacaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = HistoricoTransacao
        fields = '__all__'
