from django.contrib import admin

from .models import Campeonato, Time, Jogo
from core.network.football import API


@admin.register(Campeonato)
class CampeonatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pais', 'tipo', 'ativo', 'temporada_atual')
    search_fields = ('nome', 'pais', 'tipo')
    actions = ['buscar_campeonatos', 'desativar_campeonatos', 'ativar_campeonatos']

    def buscar_campeonatos(self, _, queryset):
        if API.buscar_e_salvar_competicoes():
            queryset = Campeonato.objects.all()
        return queryset

    def desativar_campeonatos(self, _, queryset):
        queryset.update(ativo=False)

    def ativar_campeonatos(self, _, queryset):
        queryset.update(ativo=True)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'id_externo', 'logo')
    search_fields = ('nome', )


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ('time_casa', 'time_fora', 'status', 'data', 'placar_casa',
                    'placar_fora', 'vencedor', 'campeonato')
    list_filter = ['status', 'data']
    actions_on_top = ['buscar_e_salvar_jogos']
    actions = ['atualizar_resultados']

    def buscar_e_salvar_jogos(self, _, queryset):
        campeonatos = Campeonato.objects.filter(ativo=True)
        if API.buscar_e_salvar_jogos(campeonatos):
            queryset = Jogo.objects.all()
        return queryset

    def atualizar_resultados(self, _, queryset):
        if API.atualizar_resultados(queryset):
            queryset = Jogo.objects.all()
        return queryset