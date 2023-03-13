from django.db import models

from core.models import BaseModel
from . import VENCEDOR_CHOICES


class Campeonato(BaseModel):

    nome = models.CharField("Nome", max_length=75)
    pais = models.CharField('País', max_length=75)
    tipo = models.CharField('Tipo', max_length=75, null=True, blank=True)
    id_externo = models.CharField('ID externo', max_length=25, null=True, blank=True)
    logo = models.URLField(validators='Logo', null=True, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    temporada_atual = models.CharField('Temporada', max_length=75)

    class Meta:
        verbose_name = "Campeonato"
        verbose_name_plural = "Campeonatos"

    def __str__(self):
        return self.nome


class Time(BaseModel):

    id_externo = models.CharField('ID externo', max_length=50)
    nome = models.CharField('Nome', max_length=50)
    logo = models.URLField('Logo', max_length=200)

    def __str__(self) -> str:
        return self.nome


class Jogo(BaseModel):

    id_externo = models.CharField('ID externo', max_length=50) 
    time_casa = models.ForeignKey(Time, verbose_name="Time casa", on_delete=models.CASCADE,
                                 related_name='jogos_casa')
    time_fora = models.ForeignKey(Time, verbose_name="Time fora", on_delete=models.CASCADE,
                                 related_name='jogos_fora')
    status = models.CharField('Status', max_length=50)
    data = models.DateTimeField('Data')
    placar_casa = models.IntegerField('Placar casa', null=True, blank=True)
    placar_fora = models.IntegerField('Placar Fora', null=True, blank=True)
    vencedor = models.CharField(max_length=5, choices=VENCEDOR_CHOICES.items(), null=True, blank=True)
    campeonato = models.ForeignKey(Campeonato, verbose_name='Campeonato',
                                   on_delete=models.PROTECT, related_name='jogos')

    class Meta:
        verbose_name = "Jogo"
        verbose_name_plural = "Jogos"

    @property
    def placar(self):
        if self.placar_casa and self.placar_fora:
            return  f'{self.time_casa} {self.placar_casa} vs {self.placar_fora} {self.time_fora}'
        return str(self)

    def __str__(self):
        return f'{self.time_casa} vs {self.time_fora}'
