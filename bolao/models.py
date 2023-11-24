import os
from decimal import Decimal
from typing import List
from django.utils import timezone
from django.db import models, transaction
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

from core.models import BaseModel
from usuario.models import Usuario
from . import VENCEDOR_CHOICES, STATUS_BOLAO, STATUS_JOGO_FINALIZADO_API

from core.utils import gerar_codigo, get_taxa_banca


class Campeonato(BaseModel):

    nome = models.CharField("Nome", max_length=75)
    pais = models.CharField('País', max_length=75)
    tipo = models.CharField('Tipo', max_length=75, null=True, blank=True)
    id_externo = models.CharField('ID externo', max_length=25, null=True, blank=True, unique=True)
    logo = models.URLField('Logo', null=True, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    temporada_atual = models.CharField('Temporada', max_length=75)

    class Meta:
        verbose_name = "Campeonato"
        verbose_name_plural = "Campeonatos"
        ordering = ['-ativo', 'nome']

    def __str__(self):
        return self.nome


class Time(BaseModel):

    id_externo = models.CharField('ID externo', max_length=50, unique=True)
    nome = models.CharField('Nome', max_length=50)
    logo = models.URLField('Logo', max_length=200)

    class Meta:
        verbose_name = "Time"
        verbose_name_plural = "Times"
        ordering = ['nome']

    def __str__(self) -> str:
        return self.nome


class Jogo(BaseModel):

    id_externo = models.CharField('ID externo', max_length=50, unique=True)
    time_casa = models.ForeignKey(Time, verbose_name="Time casa", on_delete=models.CASCADE,
                                  related_name='jogos_casa')
    time_fora = models.ForeignKey(Time, verbose_name="Time fora", on_delete=models.CASCADE,
                                  related_name='jogos_fora')
    status = models.CharField('Status', max_length=50)
    data = models.DateTimeField('Data')
    placar_casa = models.IntegerField('Placar casa', null=True, blank=True)
    placar_fora = models.IntegerField('Placar Fora', null=True, blank=True)
    vencedor = models.CharField(max_length=6, choices=VENCEDOR_CHOICES.items(), null=True, blank=True)
    campeonato = models.ForeignKey(Campeonato, verbose_name='Campeonato',
                                   on_delete=models.PROTECT, related_name='jogos')

    class Meta:
        verbose_name = "Jogo"
        verbose_name_plural = "Jogos"
        ordering = ['-data', 'status']

    @property
    def placar(self):
        if self.placar_casa and self.placar_fora:
            return f'{self.time_casa} {self.placar_casa} vs {self.placar_fora} {self.time_fora}'
        return str(self)

    def acertou_palpite(self, casa: int, fora: int) -> bool:
        if self.placar_casa is None or self.placar_fora is None:
            return None
        return casa == self.placar_casa and fora == self.placar_fora

    @property
    def finalizado(self):
        return self.status in STATUS_JOGO_FINALIZADO_API

    def __str__(self):
        return f'{self.time_casa} vs {self.time_fora}'


class Bolao(BaseModel):

    criador = models.ForeignKey(Usuario, verbose_name="Criador", on_delete=models.PROTECT, related_name='boloes')
    valor_palpite = models.DecimalField("Valor bilhete", max_digits=5, decimal_places=2,
                                        validators=[MaxValueValidator(Decimal(os.getenv('MAX_PALPITE'))),
                                                    MinValueValidator(Decimal(os.getenv('MIN_PALPITE')))])
    codigo = models.CharField("Código", max_length=25, default=gerar_codigo)
    jogos = models.ManyToManyField(Jogo, verbose_name="Jogos", related_name='boloes')
    estorno = models.BooleanField("Estorno", default=False)
    taxa_banca = models.FloatField("Taxa banca", default=get_taxa_banca)
    taxa_criador = models.FloatField("Taxa criador", default=0,
                                     validators=[MaxValueValidator(float(os.getenv('MAX_TAXA_CRIADOR'))),
                                                 MinValueValidator(float(os.getenv('MIN_TAXA_CRIADOR')))])
    bilhetes_minimos = models.PositiveIntegerField("Palpites mínimos", default=0)
    status = models.CharField(max_length=20, choices=STATUS_BOLAO.items(), default=STATUS_BOLAO['ATIVO'])

    class Meta:
        verbose_name = 'Bolão'
        verbose_name_plural = 'Bolões'

    def buscar_vencedores(self):
        return [bilhete.usuario for bilhete in self.bilhetes.all() if bilhete.acertou]

    def retirar_banca_e_criador(self) -> Decimal:
        """Retorna o valor restante da subtração"""
        total_bolao = self.bilhetes.count() * self.valor_palpite
        valor_banca = Decimal(self.taxa_banca / 100).quantize(Decimal('.01')) * total_bolao
        valor_criador = Decimal(self.taxa_criador / 100).quantize(Decimal('.01')) * total_bolao
        self.criador.carteira.depositar(valor_criador)
        banca = Usuario.objects.get(id=os.getenv('ID_CARTEIRA_BANCA'))
        banca.carteira.depositar(valor_banca)
        return total_bolao - (valor_banca + valor_criador)

    def pagar_vencedores(self, vencedores: List[Usuario]):
        """Usar quando a vencedores."""
        liquido = self.retirar_banca_e_criador()
        ganho = liquido / len(vencedores)
        for vencedor in vencedores:
            vencedor.carteira.depositar(ganho)

    def estornar_bolao(self):
        """Usar quando não a vencedores e estorno está ativado."""
        liquido = self.retirar_banca_e_criador()
        ganho = liquido / self.bilhetes.count()
        for bilhete in self.bilhetes.all():
            bilhete.usuario.carteira.depositar(ganho)

    def dividir_entre_banca_e_criador(self):
        """Usar quando não a vencedores e estorno não está ativado."""
        ganho = self.retirar_banca_e_criador()
        self.criador.carteira.depositar(ganho)

    @transaction.atomic
    def cancelar_bolao(self):
        for bilhete in self.bilhetes.all():
            bilhete.usuario.carteira.depositar(self.valor_palpite)
        self.status = STATUS_BOLAO['CANCELADO']
        self.save()

    @transaction.atomic
    def finalizar_bolao(self):
        if self.jogos_finalizados and self.status != STATUS_BOLAO['FINALIZADO']:
            vencedores = self.buscar_vencedores()
            if self.bilhetes_minimos > self.bilhetes.count():
                self.cancelar_bolao()
                self.status = STATUS_BOLAO['CANCELADO']
            elif len(vencedores) > 0:
                self.pagar_vencedores(vencedores)
                self.status = STATUS_BOLAO['FINALIZADO']
            elif len(vencedores) == 0 and self.estorno:
                self.estornar_bolao()
                self.status = STATUS_BOLAO['FINALIZADO']
            elif len(vencedores) == 0 and not self.estorno:
                self.dividir_entre_banca_e_criador()
                self.status = STATUS_BOLAO['FINALIZADO']
            self.save()

    @property
    def status_atualizado(self):
        for jogo in self.jogos.all():
            if jogo.data <= timezone.now():
                return STATUS_BOLAO['JOGO INICIADO']
        return self.status

    @property
    def jogos_finalizados(self):
        return any([jogo.finalizado for jogo in self.jogos.all()])

    def __str__(self):
        return f'Aposta: {self.valor_palpite}|Código: {self.codigo}'


class Bilhete(BaseModel):

    usuario = models.ForeignKey(Usuario, verbose_name="Usuário", on_delete=models.PROTECT, related_name='bilhetes')
    bolao = models.ForeignKey(Bolao, verbose_name="Bolão", on_delete=models.PROTECT, related_name='bilhetes')

    class Meta:
        verbose_name = 'Bilhete'
        verbose_name_plural = 'Bilhetes'

    @property
    def acertou(self):
        return all([bilhete.acertou for bilhete in self.palpites.all()])

    def clean(self) -> None:
        if not self.usuario.carteira.saque_valido(self.bolao.valor_palpite):
            raise ValidationError("Saldo insuficiente.")
        if self.bolao.status != STATUS_BOLAO['ATIVO']:
            raise ValidationError(f"Não é possível dar bilhetes pois o bolão {self.bolao.status.lower()}")
        return super().clean()

    def save(self, **kwargs) -> None:
        self.usuario.carteira.saque(self.bolao.valor_palpite)
        return super().save(**kwargs)

    def __str__(self) -> str:
        return f'{self.usuario.nome_formatado}|{self.bolao}'


class Palpite(models.Model):

    jogo = models.ForeignKey(Jogo, verbose_name="Jogo", on_delete=models.PROTECT, related_name='palpites')
    bilhete = models.ForeignKey(Bilhete, verbose_name="Bilhete", on_delete=models.PROTECT, related_name='palpites')
    placar_casa = models.IntegerField('Placar casa')
    placar_fora = models.IntegerField('Placar Fora')

    class Meta:
        verbose_name = 'Palpite'
        verbose_name_plural = 'Palpites'

    @property
    def acertou(self):
        return self.jogo.acertou_palpite(self.placar_casa, self.placar_fora)

    def __str__(self) -> str:
        return f'{self.jogo.time_casa} {self.placar_casa} vs {self.placar_fora} {self.jogo.time_fora}'
