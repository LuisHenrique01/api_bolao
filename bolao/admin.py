from django.contrib import admin

from .models import Campeonato
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
