from django.test import TestCase
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Campeonato, Time, Jogo, Bolao, Bilhete
from datetime import datetime, timedelta
from usuario.factories.usuario import CarteiraFactory, EnderecoFactory, PermissoesNotificacaoFactory, UsuarioFactory


class CampeonatoTest(TestCase):

    def test_str(self):
        campeonato = Campeonato(nome="Campeonato A")
        self.assertEqual(str(campeonato), "Campeonato A")

    def test_ativo(self):
        campeonato_ativo = Campeonato(nome="Campeonato Ativo", ativo=True)
        campeonato_inativo = Campeonato(nome="Campeonato Inativo", ativo=False)
        self.assertTrue(campeonato_ativo.ativo)
        self.assertFalse(campeonato_inativo.ativo)


class TimeTest(TestCase):

    def test_str(self):
        time = Time.objects.create(nome="Time A", id_externo="1", logo="https://localhost:8000/logo1")
        self.assertEqual(str(time), "Time A")


class JogoTest(TestCase):

    def setUp(self):
        campeonato = Campeonato.objects.create(nome="Campeonato A", pais="Brasil", temporada_atual="2023")
        time_casa = Time.objects.create(nome="Time A", id_externo="1", logo="https://localhost:8000/logo1")
        time_fora = Time.objects.create(nome="Time B", id_externo="2", logo="https://localhost:8000/logo2")
        self.jogo = Jogo.objects.create(id_externo="1", time_casa=time_casa, time_fora=time_fora, status="AG",
                                        data=datetime.now() + timedelta(days=1), placar_casa=1, placar_fora=2,
                                        campeonato=campeonato)

    def test_str(self):
        self.assertEqual(str(self.jogo), "Time A vs Time B")

    def test_placar(self):
        self.assertEqual(self.jogo.placar, "Time A 1 vs 2 Time B")

    def test_acertou_palpite(self):
        self.assertTrue(self.jogo.acertou_palpite(1, 2))
        self.assertFalse(self.jogo.acertou_palpite(0, 1))


class BolaoModelTestCase(TestCase):

    def setUp(self):
        endereco = EnderecoFactory()
        permissoes = PermissoesNotificacaoFactory()
        carteira = CarteiraFactory()
        usuario = UsuarioFactory(endereco=endereco, permissoes=permissoes, carteira=carteira)
        self.criador = usuario
        campeonato = Campeonato.objects.create(nome="Campeonato A", pais="Brasil", temporada_atual="2023")
        time_casa = Time.objects.create(nome="Time A", id_externo="1", logo="https://localhost:8000/logo1")
        time_fora = Time.objects.create(nome="Time B", id_externo="2", logo="https://localhost:8000/logo2")
        self.jogo1 = Jogo.objects.create(id_externo="1", time_casa=time_casa, time_fora=time_fora, status="AG",
                                         data=datetime.now() + timedelta(days=1), placar_casa=1, placar_fora=0,
                                         campeonato=campeonato)
        self.jogo2 = Jogo.objects.create(id_externo="2", time_casa=time_casa, time_fora=time_fora, status="AG",
                                         data=datetime.now() + timedelta(days=1), placar_casa=2, placar_fora=1,
                                         campeonato=campeonato)

    def test_valor_palpite_must_be_within_valid_range(self):
        bolao = Bolao(criador=self.criador, valor_palpite=Decimal('5'))
        self.assertIsNone(bolao.full_clean())
        bolao.valor_palpite = Decimal('1')
        with self.assertRaises(ValidationError):
            bolao.full_clean()

    def test_taxa_criador_must_be_within_valid_range(self):
        bolao = Bolao(criador=self.criador, valor_palpite=Decimal('10.00'), taxa_criador=50)
        with self.assertRaises(ValidationError):
            bolao.full_clean()

    def test_buscar_vencedores(self):
        endereco = EnderecoFactory()
        permissoes1 = PermissoesNotificacaoFactory()
        permissoes2 = PermissoesNotificacaoFactory()
        usuario1 = UsuarioFactory(endereco=endereco, permissoes=permissoes1)
        usuario2 = UsuarioFactory(endereco=endereco, permissoes=permissoes2)
        usuario1.carteira.depositar(Decimal('50.00'))
        usuario2.carteira.depositar(Decimal('50.00'))
        bolao = Bolao.objects.create(criador=self.criador, valor_palpite=Decimal('10.00'))
        palpite1 = Bilhete.objects.create(usuario=usuario1, bolao=bolao)
        palpite2 = Bilhete.objects.create(usuario=usuario2, bolao=bolao)
        palpite1.palpites.create(jogo=self.jogo1, placar_casa=1, placar_fora=0)
        palpite1.palpites.create(jogo=self.jogo2, placar_casa=2, placar_fora=1)
        palpite2.palpites.create(jogo=self.jogo1, placar_casa=2, placar_fora=1)
        palpite2.palpites.create(jogo=self.jogo2, placar_casa=1, placar_fora=1)
        vencedores = bolao.buscar_vencedores()
        self.assertEqual(vencedores, [usuario1])

    def test_buscar_vencedores_without_palpites(self):
        bolao = Bolao.objects.create(criador=self.criador, valor_palpite=Decimal('10.00'))
        vencedores = bolao.buscar_vencedores()
        self.assertEqual(vencedores, [])


'''
    def test_pagar_vencedores(self):
        endereco = EnderecoFactory()
        permissoes = PermissoesNotificacaoFactory()
        carteira1 = CarteiraFactory()
        carteira2 = CarteiraFactory()
        usuario1 = UsuarioFactory(endereco=endereco, permissoes=permissoes, carteira=carteira1)
        usuario2 = UsuarioFactory(endereco=endereco, permissoes=permissoes, carteira=carteira2)
        bolao = Bolao.objects.create(criador=self.criador, valor_palpite=Decimal('10.00'))
        bolao
        palpite1 = Bilhete.objects.create(usuario=usuario1, bolao=bolao)
        palpite2 = Bilhete.objects.create(usuario=usuario2, bolao=bolao)
        palpite1.palpites.create(jogo=self.jogo1, placar_casa=1, placar_fora=0)
        palpite1.palpites.create(jogo=self.jogo2, placar_casa=2, placar_fora=1)
        palpite2.palpites.create(jogo=self.jogo1, placar_casa=0, placar_fora=0)
'''
