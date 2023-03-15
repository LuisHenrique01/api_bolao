from decimal import Decimal
import os
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from core.models import BaseModel
from usuario.models import Usuario
from . import VENCEDOR_CHOICES

from .utils import gerar_codigo, get_taxa_banca


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

    def __str__(self):
        return f'{self.time_casa} vs {self.time_fora}'


class Bolao(BaseModel):

    criador = models.ForeignKey(Usuario, verbose_name="Criador", on_delete=models.PROTECT, related_name='boloes')
    valor_palpite = models.DecimalField("Valor palpite", max_digits=5, decimal_places=2,
                                        validators=[MaxValueValidator(Decimal(os.getenv('MAX_PALPITE'))),
                                                    MinValueValidator(Decimal(os.getenv('MIN_PALPITE')))])
    codigo = models.CharField("Código", max_length=25, default=gerar_codigo)
    jogos = models.ManyToManyField(Jogo, verbose_name="Jogos", related_name='boloes')

    class Meta:
        verbose_name = 'Bolão'
        verbose_name_plural = 'Bolões'

    def __str__(self):
        return f'Aposta: {self.valor_palpite}|Código: {self.codigo}'


class Palpite(BaseModel):

    usuario = models.ForeignKey(Usuario, verbose_name="Usuário", on_delete=models.PROTECT, related_name='palpites')
    bolao = models.ForeignKey(Bolao, verbose_name="Bolão", on_delete=models.PROTECT, related_name='palpites')

    class Meta:
        verbose_name = 'Palpite'
        verbose_name_plural = 'Palpites'

    def __str__(self) -> str:
        return f'{self.usuario.nome_formatado}|{self.bolao}'


class PalpitePlacar(models.Model):

    jogo = models.ForeignKey(Jogo, verbose_name="Jogo", on_delete=models.PROTECT, related_name='palpites_placar')
    palpite = models.ForeignKey(Palpite, verbose_name="Palpite", on_delete=models.PROTECT, related_name='placares')
    placar_casa = models.IntegerField('Placar casa')
    placar_fora = models.IntegerField('Placar Fora')

    class Meta:
        verbose_name = 'Placar'
        verbose_name_plural = 'Placares'

    def __str__(self) -> str:
        f'{self.jogo.time_casa} {self.placar_casa} vs {self.placar_fora} {self.jogo.time_fora}'
