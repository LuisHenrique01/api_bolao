from datetime import datetime, timedelta
from bolao import STATUS_JOGO_FINALIZADO_API
from celery import shared_task, current_app

from .models import Jogo
from core.network.football import API


@shared_task
def conferir_resultado(id_externo: str):
    jogo = Jogo.objects.get(id_externo=id_externo)
    API.atualizar_resultados(jogo, many=False)
    jogo = Jogo.objects.get(id_externo=id_externo) # Mandar para finalização de bolão caso tenha bolão.
    if jogo.status in STATUS_JOGO_FINALIZADO_API.split('-'):
        pass # Chamar task de validar bolões
    else:
        current_app.send_task('bolao.tasks.conferir_resultado', args=(id_externo, ), countdown=600)


def