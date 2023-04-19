from datetime import date, timedelta
import os
from typing import List, Union
import requests
from django.utils import timezone
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from bolao import VENCEDOR_CHOICES, STATUS_JOGO_FINALIZADO_API
from bolao.models import Campeonato, Jogo, Time


class API:
    api_using = 'IO'
    url = "https://v3.football.api-sports.io/"
    headers = {"x-apisports-key": os.getenv("KEY_FOOTBALL_API_IO")}

    @classmethod
    def set_rapid_api(cls):
        setattr(cls, 'api_using', 'RAPID_API')
        setattr(cls, 'url', "https://api-football-v1.p.rapidapi.com/v3/")
        setattr(cls, 'headers', {"x-rapidapi-host": "v3.football.api-sports.io",
                                 "x-rapidapi-key": os.getenv('KEY_FOOTBALL_DATA')})

    @staticmethod
    def get_current(seasons: List[dict]) -> str:
        for season in seasons:
            if season['current']:
                return str(season['year'])

    @classmethod
    def buscar_e_salvar_competicoes(cls):
        params = {"country": "Brazil"}
        response = requests.get(cls.url + 'leagues', headers=cls.headers, params=params)
        if response.status_code == 200:
            competicoes = response.json()["response"]

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

            Campeonato.objects.bulk_create(campeonatos, update_conflicts=True,
                                           update_fields=['temporada_atual', 'logo'],
                                           unique_fields=['id_externo'])
            return True
        if cls.api_using == 'RAPID_API':
            return False
        cls.set_rapid_api()
        return cls.buscar_e_salvar_competicoes()

    @classmethod
    def salvar_jogo(cls, jogo: dict, campeonato: Campeonato) -> Jogo:
        time_casa = cls.salvar_time(jogo["teams"]["home"]["id"], jogo["teams"]["home"]["name"],
                                    jogo["teams"]["home"]["logo"])
        time_fora = cls.salvar_time(jogo["teams"]["away"]["id"], jogo["teams"]["away"]["name"],
                                    jogo["teams"]["away"]["logo"])

        id_externo = jogo["fixture"]["id"]
        status = jogo["fixture"]["status"]["short"]
        data = timezone.datetime.strptime(jogo["fixture"]["date"], "%Y-%m-%dT%H:%M:%S-03:00")
        placar_casa = jogo["goals"]["home"]
        placar_fora = jogo["goals"]["away"]
        vencedor = cls.obter_vencedor(placar_casa, placar_fora)

        new_jogo, _ = Jogo.objects.update_or_create(
            id_externo=id_externo,
            defaults={
                "time_casa": time_casa,
                "time_fora": time_fora,
                "status": status,
                "data": data,
                "placar_casa": placar_casa,
                "placar_fora": placar_fora,
                "vencedor": vencedor,
                "campeonato": campeonato,
            }
        )
        return new_jogo

    @classmethod
    def buscar_jogos(cls, campeonato: Campeonato):
        today = date.today()
        parametros = {
            "timezone": "America/Sao_Paulo",
            "status": "NS",
            "season": campeonato.temporada_atual,
            "league": campeonato.id_externo,
            "from": str(today),
            "to": str(today + timedelta(days=int(os.getenv("DAYS_GET_JOGOS"))))
        }
        response = requests.get(cls.url + 'fixtures', headers=cls.headers, params=parametros)
        if response.status_code == 200:
            return response.json()["response"]
        if cls.api_using == 'RAPID_API':
            raise Exception(f"Failed to retrieve fixtures. Status code: {response.status_code}")
        cls.set_rapid_api()
        return cls.buscar_e_salvar_competicoes()

    @classmethod
    def buscar_e_salvar_jogos(cls, campeonatos: List[Campeonato]) -> bool:
        criados = []
        for campeonato in campeonatos:
            jogos = cls.buscar_jogos(campeonato)
            for jogo in jogos:
                criados.append(cls.salvar_jogo(jogo, campeonato))
        return criados

    @classmethod
    def salvar_time(cls, id_externo: int, nome: str, logo: str):
        time, _ = Time.objects.get_or_create(id_externo=str(id_externo), defaults={
            "nome": nome,
            "logo": logo
        })
        return time

    @staticmethod
    def obter_vencedor(placar_casa: int, placar_fora: int) -> str:
        if placar_casa is None and placar_fora is None:
            return None
        elif placar_casa > placar_fora:
            return VENCEDOR_CHOICES["CASA"]
        elif placar_casa < placar_fora:
            return VENCEDOR_CHOICES["FORA"]
        else:
            return VENCEDOR_CHOICES['EMPATE']

    @classmethod
    def salvar_resultdo(cls, data: dict, jogo: Jogo):
        placar_casa = data["score"]["fulltime"]["home"]
        placar_fora = data["score"]["fulltime"]["away"]
        jogo.status = data["fixture"]["status"]["short"]
        jogo.vencedor = cls.obter_vencedor(placar_casa, placar_fora)
        jogo.placar_casa = placar_casa
        jogo.placar_fora = placar_fora
        jogo.save()

    @classmethod
    def atualizar_resultados(cls, jogos: Union[QuerySet, Jogo], many: bool = True) -> bool:
        parametros = {"timezone": "America/Sao_Paulo", "status": STATUS_JOGO_FINALIZADO_API}
        if many:
            values = jogos.values('id_externo')
            for count in range(0, len(values), 20):
                parametros['ids'] = '-'.join((jogo['id_externo'] for jogo in values[count:count+20:]))
                response = requests.get(cls.url + 'fixtures', headers=cls.headers, params=parametros)
                if response.status_code == 200:
                    for data in response.json()["response"]:
                        cls.salvar_resultdo(data, jogos.get(id_externo=data["fixture"]["id"]))
                else:
                    break
            else:
                # Se o break não for chamado o for cai no else
                return True
            if cls.api_using == 'RAPID_API':
                raise Exception(f"Failed to retrieve fixtures. Status code: {response.status_code}")
            cls.set_rapid_api()
            return cls.atualizar_resultados(jogos, many)
        else:
            parametros['id'] = jogos.id_externo
            response = requests.get(cls.url + 'fixtures', headers=cls.headers, params=parametros)
            if response.status_code == 200:
                data = response.json()["response"][0]
                cls.salvar_resultdo(data, jogos)
                return True
            else:
                if cls.api_using == 'RAPID_API':
                    raise Exception(f"Failed to retrieve fixtures. Status code: {response.status_code}")
                cls.set_rapid_api()
                return cls.atualizar_resultados(jogos, many)
