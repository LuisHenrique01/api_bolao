from celery import current_app
from django.contrib import admin, messages

from . import STATUS_JOGO_FINALIZADO_API, STATUS_BOLAO

from .models import Campeonato, Time, Jogo, Bolao, Bilhete, Palpite
from .forms import PalpitePlacarForm
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
    list_display = ['time_casa', 'time_fora', 'status', 'data', 'placar_casa',
                    'placar_fora', 'vencedor', 'campeonato']
    list_filter = ['status', 'data']
    actions = ['atualizar_resultados', 'buscar_e_salvar_jogos']

    def buscar_e_salvar_jogos(self, _, queryset):
        campeonatos = Campeonato.objects.filter(ativo=True)
        if API.buscar_e_salvar_jogos(campeonatos):
            queryset = Jogo.objects.all()
        return queryset

    def atualizar_resultados(self, _, queryset):
        if API.atualizar_resultados(queryset):
            for jogo in queryset:
                current_app.send_task('bolao.tasks.finalizar_boloes', args=(jogo.id_externo, ))
            queryset = Jogo.objects.all()
        return queryset


@admin.register(Bolao)
class BolaoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'criador', 'valor_palpite', 'get_jogos', 'estorno', 'taxa_criador',
                    'bilhetes_minimos', 'taxa_banca', 'status']
    list_filter = ['criador', 'estorno']
    search_fields = ['codigo', 'criador', 'valor_palpite']
    actions = ['cancelar_bolao', 'finalizar_bolao']

    def get_jogos(self, obj):
        return ''.join((str(j) for j in obj.jogos.all()))

    def cancelar_bolao(self, request, queryset):
        for bolao in queryset:
            if getattr(request.user, 'is_superuser', False) or bolao.criador.id == request.user.id:
                if bolao.status == STATUS_BOLAO['FINALIZADO'] or bolao.status == STATUS_BOLAO['CANCELADO']:
                    messages.error(request, f"Erro ao cancelar o bolão {bolao.codigo}. \
                                   O bolão já está {bolao.status.lower()}!")
                else:
                    bolao.cancelar_bolao()
                    messages.success(request, f"Sucesso ao cancelar o bolão {bolao.codigo}.")
            else:
                messages.error(request, f"Erro ao cancelar o bolão {bolao.codigo}. Você não tem permissão!")

    def finalizar_bolao(self, request, queryset):
        if getattr(request.user, 'is_superuser', False):
            status = tuple(STATUS_JOGO_FINALIZADO_API.split('-'))
            for bolao in queryset:
                if all([jogo.status in status for jogo in bolao.jogos.all()]):
                    if bolao.status == STATUS_BOLAO['FINALIZADO'] or bolao.status == STATUS_BOLAO['CANCELADO']:
                        messages.error(request, f"Erro ao finalizar o bolão {bolao.codigo}. \
                                       O bolão já está {bolao.status.lower()}!")
                    else:
                        bolao.finalizar_bolao()
                        messages.success(request, f"Sucesso ao finalizar o bolão {bolao.codigo}.")
                else:
                    messages.error(request, f"Erro ao cancelar o bolão {bolao.codigo}. \
                                   Nem todos os jogos foram finalizados!")


class PalpitePlacarInline(admin.TabularInline):
    model = Palpite
    form = PalpitePlacarForm


@admin.register(Bilhete)
class PalpiteAdmin(admin.ModelAdmin):
    inlines = (PalpitePlacarInline, )
    list_display = ['bolao', 'usuario']
