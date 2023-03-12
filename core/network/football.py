from datetime import datetime, timedelta
import os
import requests
import json
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from bolao.models import Campeonato, Jogo, Time

class API:
    url = "https://v3.football.api-sports.io/"
    headers_io = {"x-apisports-key": os.getenv("KEY_FOOTBALL_API_IO")}
    headers_rapid = {"x-rapidapi-host": "v3.football.api-sports.io",
                     "x-rapidapi-key": os.getenv('KEY_FOOTBALL_DATA')}
    
    @classmethod
    def buscar_e_salvar_competicoes(cls):
        params = {"country": "Brazil"}
        response = requests.get(cls.url + 'leagues', headers=cls.headers_io, params=params)
        competicoes = json.loads(response.text)["response"]

        campeonatos = []
        for competicao in competicoes:
            nome = competicao["league"]["name"]
            tipo = competicao["league"]["type"]
            pais = competicao["country"]["name"]
            id_externo = competicao["league"]["id"]
            logo = competicao["league"]["logo"]
            temporada_atual = cls.get_current(competicao['seasons'])

            validator = URLValidator()
            try:
                validator(logo)
            except ValidationError:
                logo = None

            campeonatos.append(Campeonato(
                nome=nome,
                pais=pais,
                tipo=tipo,
                id_externo=id_externo,
                logo=logo,
                temporada_atual=temporada_atual
            ))

        Campeonato.objects.bulk_create(campeonatos)

    @staticmethod
    def get_current(seasons):
        for season in seasons:
            if season['current']:
                return str(season['year'])

    @classmethod
    def buscar_e_salvar_jogos(cls):
        dias_para_buscar = 7
        data_inicio = datetime.utcnow().date().strftime("%Y-%m-%d")
        data_fim = (datetime.utcnow().date() + timedelta(days=dias_para_buscar)).strftime("%Y-%m-%d")

        parametros = {"status": "NS", "timezone": "America/Sao_Paulo",
                      "from": data_inicio, "to": data_fim}
        campeonatos = Campeonato.objects.filter(ativo=True)
        for campeonato in campeonatos:
            parametros["season"] = campeonato.temporada_atual
            parametros["league"] = campeonato.id_externo
            response = requests.get(cls.url + 'fixtures', headers=cls.headers_io, params=parametros)
            jogos = response.json()["response"]

            for jogo in jogos:
                time_casa = cls.salvar_time(jogo["teams"]["home"]["name"], jogo["league"]["country"])
                time_fora = cls.salvar_time(jogo["teams"]["away"]["name"], jogo["league"]["country"])

                campeonato_id_externo = jogo["league"]["id"]
                campeonato = Campeonato.objects.get(id_externo=campeonato_id_externo)

                id_externo = jogo["fixture"]["id"]
                status = jogo["fixture"]["status"]["short"]
                data = datetime.strptime(jogo["fixture"]["date"], "%Y-%m-%dT%H:%M:%S+00:00")
                placar_casa = jogo["goals"]["home"]
                placar_fora = jogo["goals"]["away"]
                vencedor = cls.obter_vencedor(time_casa, time_fora, placar_casa, placar_fora)

                Jogo.objects.update_or_create(
                    id_externo=id_externo,
                    defaults={
                        "timeCasa": time_casa,
                        "timeFora": time_fora,
                        "status": status,
                        "data": data,
                        "placarCasa": placar_casa,
                        "placarFora": placar_fora,
                        "vencedor": vencedor,
                        "campeonato": campeonato,
                    }
                )

    @classmethod
    def salvar_time(cls, nome, pais):
        time, _ = Time.objects.get_or_create(nome=nome, pais=pais)
        return time
    
    @staticmethod
    def obter_vencedor(time_casa, time_fora, placar_casa, placar_fora):
        if placar_casa > placar_fora:
            return time_casa
        elif placar_casa < placar_fora:
            return time_fora
        else:
            return None
