import os
from decimal import Decimal
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from core.communications import Email
from core.models import HistoricoTransacao, AsaasInformations

from usuario.models import Carteira, Endereco, PermissoesNotificacao, Usuario, ContaExternaUsuario
from core.custom_exception import UsuarioNaoEncontrado


class EnderecoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Endereco
        fields = '__all__'


class PermissoesSerializer(serializers.ModelSerializer):

    class Meta:
        model = PermissoesNotificacao
        fields = '__all__'


class ContaExternaUsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContaExternaUsuario
        fields = ['code_banco', 'agencia', 'tipo_conta', 'num_conta', 'digito']


class CarteiraSerializer(serializers.ModelSerializer):

    valor = serializers.DecimalField(max_digits=9, decimal_places=2, required=False)
    conta = ContaExternaUsuarioSerializer(required=False)

    class Meta:
        model = Carteira
        fields = '__all__'
        read_only_fields = ['saldo', 'bloqueado']

    def validate_valor(self, value):
        if 'conta' in self.initial_data:
            valor_minimo = Decimal(os.getenv('MIN_SAQUE'))
        else:
            valor_minimo = Decimal(os.getenv('MIN_DEPOSITO'))
        if value < valor_minimo:
            raise serializers.ValidationError('Valor abaixo do permitido.')
        return value

    def depositar(self, carteira: Carteira):
        transaction = carteira.solicitar_cash_in(self.validated_data['valor'])
        return transaction

    def sacar(self, carteira: Carteira):
        return carteira.solicitar_cash_out(self.validated_data['valor'],
                                           self.validated_data['conta'])


class CriarUsuarioSerializer(serializers.ModelSerializer):

    endereco = EnderecoSerializer()
    permissoes = PermissoesSerializer()
    carteira = CarteiraSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['email', 'cpf', 'nome', 'password', 'data_nascimento', 'telefone',
                  'endereco', 'permissoes', 'carteira']
        read_only_fields = ['id']
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

    def recuperar_senha(self):
        email = self.validated_data.get("email")
        sms = self.validated_data.get("sms")
        try:
            if email:
                usuario = Usuario.objects.get(email=email)
                codigo = usuario.permissoes.criar_codigo('email')
                Email.recuperar_senha(usuario.email, codigo.codigo, usuario.nome_formatado)
            if sms:
                raise NotImplementedError('Ainda não estamos disponibilizando esse serviço.')
        except ObjectDoesNotExist:
            raise UsuarioNaoEncontrado()

    def validar_usuario(self):
        email = self.validated_data.get("email")
        sms = self.validated_data.get("sms")
        try:
            if email:
                usuario = Usuario.objects.get(email=email)
                codigo = usuario.permissoes.criar_codigo('email')
                Email.validar_usuario(usuario.email, codigo.codigo, usuario.nome_formatado)
            if sms:
                raise NotImplementedError('Ainda não estamos disponibilizando esse serviço.')
        except ObjectDoesNotExist:
            raise UsuarioNaoEncontrado()


class UsuarioSerializer(serializers.ModelSerializer):
    endereco = EnderecoSerializer()
    permissoes = PermissoesSerializer()
    carteira = CarteiraSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'cpf_marcarado', 'nome', 'nome_formatado', 'password', 'data_nascimento', 'telefone',
                  'endereco', 'permissoes', 'carteira']
        read_only_fields = ['id', 'cpf_marcarado', 'data_nascimento', 'nome_formatado']
        extra_kwargs = {'password': {'write_only': True}, 'nome': {'write_only': True}}

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


class AsaasInfosSerializer(serializers.ModelSerializer):
    pix = serializers.SerializerMethodField()

    class Meta:
        model = AsaasInformations
        fields = ['asaas_id', 'value', 'pix']

    def get_pix(self, obj):
        return obj.get_pix_infos()


class HistoricoTransacaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = HistoricoTransacao
        fields = '__all__'
