from datetime import timedelta
import os
from decimal import Decimal
from rest_framework import serializers
from django.utils import timezone

from bolao import STATUS_BOLAO
from bolao.models import Bolao, Campeonato, Jogo, Time, Palpite, Bilhete


class CampeonatoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Campeonato
        exclude = ['id_externo', 'created_at', 'updated_at']


class TimeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Time
        exclude = ['id_externo', 'created_at', 'updated_at']


class JogoSerializer(serializers.ModelSerializer):

    campeonato = CampeonatoSerializer(read_only=True)
    time_casa = TimeSerializer(read_only=True)
    time_fora = TimeSerializer(read_only=True)

    class Meta:
        model = Jogo
        exclude = ['id_externo']


class BolaoSerializer(serializers.ModelSerializer):

    qtd_palpites = serializers.SerializerMethodField()
    posivel_retorno = serializers.SerializerMethodField()
    vencedores = serializers.SerializerMethodField()
    jogos = JogoSerializer(many=True)

    class Meta:
        model = Bolao
        fields = ['id', 'criador', 'valor_palpite', 'codigo', 'jogos', 'estorno', 'taxa_banca', 'taxa_criador',
                  'bilhetes_minimos', 'status', 'qtd_palpites', 'posivel_retorno', 'vencedores']
        read_only_fields = ['id']
        extra_kwargs = {'criador': {'write_only': True}}

    def get_qtd_palpites(self, obj):
        return obj.bilhetes.count()

    def get_posivel_retorno(self, obj):
        total = obj.bilhetes.count() * obj.valor_palpite
        taxa = Decimal(round((100 - (obj.taxa_banca + obj.taxa_criador)) / 100, 2))
        return total * taxa

    def get_vencedores(self, obj):
        return [usuario.nome_formatado for usuario in obj.buscar_vencedores()]


class CriarBolaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bolao
        fields = ['criador', 'valor_palpite', 'codigo', 'jogos', 'estorno', 'taxa_criador']

    def validate_jogos(self, value):
        now = timezone.now() - timedelta(minutes=5)
        for jogo in value:
            if jogo.data <= now:
                raise serializers.ValidationError(f"O jogo {jogo} não pode ser adicionado, \
                                                  pois já iniciou ou está próximo do início.")
        return value

    def validate_valor_palpite(self, value):
        if Decimal(os.getenv('MIN_PALPITE')) > value:
            raise serializers.ValidationError("O valor do palpite está abaixo do permitido.")
        if Decimal(os.getenv('MAX_PALPITE')) < value:
            raise serializers.ValidationError("O valor do palpite está acima do permitido.")
        return value

    def validate_codigo(self, value):
        if Bolao.objects.filter(codigo=value).exclude(status=STATUS_BOLAO['CANCELADO']).exists():
            raise serializers.ValidationError("Código do bolão existente.")
        return value

    def validate_taxa_criador(self, value):
        if Decimal(os.getenv('MIN_TAXA_CRIADOR')) > value:
            raise serializers.ValidationError("O valor da taxa crieador está abaixo do permitido.")
        if Decimal(os.getenv('MAX_TAXA_CRIADOR')) < value:
            raise serializers.ValidationError("O valor da taxa crieador está acima do permitido.")
        return value


class PalpiteSerializer(serializers.ModelSerializer):

    jogo = JogoSerializer()

    class Meta:
        model = Palpite
        fields = ['jogo', 'placar_casa', 'placar_fora']


class BilheteSerializer(serializers.ModelSerializer):

    palpites = PalpiteSerializer(many=True)
    codigo_bolao = serializers.SerializerMethodField()
    status_bolao = serializers.SerializerMethodField()

    class Meta:
        model = Bilhete
        fields = ['usuario', 'bolao', 'palpites', 'acertou', 'codigo_bolao', 'status_bolao']
        read_only_fields = ['acertou']
        extra_kwargs = {'usuario': {'write_only': True}, 'bolao': {'write_only': True}}

    def get_codigo_bolao(self, obj):
        return obj.bolao.codigo

    def get_status_bolao(self, obj):
        return obj.bolao.status


class PalpiteCriarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Palpite
        fields = '__all__'

    def validate(self, attrs):
        now = timezone.now()
        if now < attrs['jogo'].data:
            return super().validate(attrs)
        raise serializers.ValidationError('Este bolão não está mais aceitando palpites.')

    def validate_placar_casa(self, value):
        if value >= 0:
            return value
        raise serializers.ValidationError('O placar do time casa deve ser maior ou igual a 0.')

    def validate_placar_fora(self, value):
        if value >= 0:
            return value
        raise serializers.ValidationError('O placar do time fora deve ser maior ou igual a 0.')


class BilheteCriarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bilhete
        fields = '__all__'

    def validate(self, attrs):
        if attrs['usuario'].carteira.saque_valido(attrs['bolao'].valor_palpite):
            return super().validate(attrs)
        raise serializers.ValidationError("Saldo insuficiente.")
