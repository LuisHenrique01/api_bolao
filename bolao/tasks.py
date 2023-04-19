from datetime import timedelta
from celery import shared_task, current_app, Task
from celery.utils.log import get_task_logger

from bolao import STATUS_JOGO_FINALIZADO_API
from .models import Bolao, Campeonato, Jogo
from core.network.football import API


logger = get_task_logger(__name__)

class BaseTaskWithRetry(Task):
    autoretry_for = (Exception, )
    retry_kwargs = {'countdown': 180}
    retry_backoff = 120
    retry_jitter = True


@shared_task(bind=True, base=BaseTaskWithRetry)
def buscar_jogos(self):
    campeonatos = Campeonato.objects.filter(ativo=True)
    criados = API.buscar_e_salvar_jogos(campeonatos)

    if len(criados) == 0:
        raise Exception()

    for jogo in criados:
        eta = jogo.data + timedelta(hours=2)
        current_app.send_task('bolao.tasks.conferir_resultado', args=(jogo.id_externo, ), eta=eta)


@shared_task(bind=True, base=BaseTaskWithRetry)
def conferir_resultado(self, id_externo: str):
    jogo = Jogo.objects.get(id_externo=id_externo)
    API.atualizar_resultados(jogo, many=False)
    jogo = Jogo.objects.get(id_externo=id_externo)

    if jogo.status not in STATUS_JOGO_FINALIZADO_API.split('-'):
        raise Exception()

    current_app.send_task('bolao.tasks.finalizar_boloes', args=(jogo.id_externo, ))


@shared_task
def finalizar_boloes(id_externo: str):
    boloes = Bolao.objects.filter(jogos__id_externo__in=[id_externo])
    for bolao in boloes:
        bolao.finalizar_bolao()