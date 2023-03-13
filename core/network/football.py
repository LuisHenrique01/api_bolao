from datetime import datetime, timedelta
import os
import requests
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from bolao import VENCEDOR_CHOICES
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
    def get_current(seasons):
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

            Campeonato.objects.bulk_create(campeonatos)
            return True
        if cls.api_using == 'RAPID_API':
            return False
        cls.set_rapid_api()
        return cls.buscar_e_salvar_competicoes()

    @classmethod
    def salvar_jogo(cls, jogo, campeonato):
        time_casa = cls.salvar_time(jogo["teams"]["home"]["name"], jogo["league"]["country"])
        time_fora = cls.salvar_time(jogo["teams"]["away"]["name"], jogo["league"]["country"])

        id_externo = jogo["fixture"]["id"]
        status = jogo["fixture"]["status"]["short"]
        data = datetime.strptime(jogo["fixture"]["date"], "%Y-%m-%dT%H:%M:%S+00:00")
        placar_casa = jogo["goals"]["home"]
        placar_fora = jogo["goals"]["away"]
        vencedor = cls.obter_vencedor(placar_casa, placar_fora)

        jogo, _ = Jogo.objects.update_or_create(
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
        return jogo

    @classmethod
    def buscar_jogos(cls, campeonato):
        parametros = {
            "season": campeonato.temporada_atual,
            "league": campeonato.id_externo,
        }
        response = requests.get(cls.url + 'fixtures', headers=cls.headers, params=parametros)
        if response.status_code == 200:
            return response.json()["response"]
        if cls.api_using == 'RAPID_API':
            raise Exception(f"Failed to retrieve fixtures. Status code: {response.status_code}")
        cls.set_rapid_api()
        return cls.buscar_e_salvar_competicoes()

    @classmethod
    def buscar_e_salvar_jogos(cls, campeonatos):
        for campeonato in campeonatos:
            jogos = cls.buscar_jogos(campeonato)
            for jogo in jogos:
                cls.salvar_jogo(jogo, campeonato)

    @classmethod
    def salvar_time(cls, nome, pais):
        time, _ = Time.objects.get_or_create(nome=nome, pais=pais)
        return time
    
    @staticmethod
    def obter_vencedor(placar_casa, placar_fora):
        if placar_casa is None and placar_fora is None:
            return None
        elif placar_casa > placar_fora:
            return VENCEDOR_CHOICES["CASA"]
        elif placar_casa < placar_fora:
            return VENCEDOR_CHOICES["FORA"]
        else:
            return VENCEDOR_CHOICES['EMPATE']

    @classmethod
    def update_game_results(cls, game: Jogo):
        response = requests.get(cls.url + f'fixtures?id={game.id_externo}', headers=cls.headers)
        if response.status_code == 200:
            data = response.json()["response"][0]
            placar_casa = data["goals"]["home"]
            placar_fora = data["goals"]["away"]
            game.status = data["fixture"]["status"]["short"]
            game.vencedor = cls.obter_vencedor(placar_casa, placar_fora)
            game.placar_casa = placar_casa
            game.placar_fora = placar_fora
            game.save()
            return True
        if cls.api_using == 'RAPID_API':
            raise Exception(f"Failed to retrieve fixtures. Status code: {response.status_code}")
        cls.set_rapid_api()
        return cls.buscar_e_salvar_competicoes()

