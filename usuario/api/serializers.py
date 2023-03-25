from rest_framework import serializers

from usuario.models import Carteira, Endereco, PermissoesNotificacao, Usuario


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


