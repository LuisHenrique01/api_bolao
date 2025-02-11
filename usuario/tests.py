import uuid
from decimal import Decimal
from django.test import TestCase
from unittest import skip
from django.db.utils import IntegrityError
from .models import PermissoesNotificacao, Endereco, Carteira, Usuario
from core.custom_exception import SaldoInvalidoException, DepositoInvalidoException


class PermissoesNotificacaoModelTest(TestCase):

    def test_str_method(self):
        permissoes_notificacao = PermissoesNotificacao.objects.create(sms=True, email=False)
        self.assertEqual(str(permissoes_notificacao), "SMS: True|E-mail: False")


class EnderecoModelTest(TestCase):

    def test_str_method(self):
        endereco = Endereco.objects.create(
            cep="00000-000",
            estado="SP",
            cidade="São Paulo",
            bairro="Centro",
            rua="Rua dos Testes",
            numero="123",
            complemento="Sala 123"
        )
        self.assertEqual(str(endereco), "CEP: 00000-000|Cidade: São Paulo")


class CarteiraModelTest(TestCase):

    def setUp(self):
        self.carteira = Carteira.objects.create()
        self.carteira2 = Carteira.objects.create()

    def test_saldo_default_value(self):
        self.assertEqual(self.carteira.saldo, Decimal("0"))

    def test_deposito_valido_interno(self):
        self.assertTrue(self.carteira.deposito_valido(Decimal("50")))
        self.assertTrue(self.carteira.deposito_valido(Decimal("9.99")))

    def test_saque(self):
        self.carteira.depositar(Decimal("100"))
        self.carteira.saque(Decimal("50"))
        self.assertEqual(self.carteira.saldo, Decimal("50"))

    def test_saque_raises_exception_when_insufficient_funds(self):
        with self.assertRaises(SaldoInvalidoException):
            self.carteira.saque(Decimal("100"))

    def test_depositar(self):
        self.carteira.depositar(Decimal("100"))
        self.assertEqual(self.carteira.saldo, Decimal("100"))

    def test_depositar_raises_exception_when_value_is_below_min_deposito(self):
        with self.assertRaises(DepositoInvalidoException):
            self.carteira.depositar(Decimal("0.50"), externo=True)

    def test_saque_valido(self):
        self.carteira2.depositar(Decimal("100"))
        # Usuário bloqueado
        self.carteira2.bloqueado = True
        self.assertFalse(self.carteira2.saque_valido(Decimal('50.00')))
        self.carteira2.bloqueado = False

        self.assertTrue(self.carteira2.saque_valido(Decimal('50.00')))
        self.assertFalse(self.carteira2.saque_valido(Decimal('200.00')))

        self.assertTrue(self.carteira2.saque_valido(Decimal('50.00'), externo=True))
        self.assertFalse(self.carteira2.saque_valido(Decimal('0.50'), externo=True))

    def test_deposito_valido_externo(self):
        self.assertTrue(self.carteira2.deposito_valido(Decimal('25.00'), externo=True))
        self.assertFalse(self.carteira2.deposito_valido(Decimal('0.50'), externo=True))

    def test_str(self):
        self.carteira.saldo = Decimal('100.00')
        self.assertEqual(str(self.carteira), 'Saldo: 100.00')

    @skip('Foi implementado')
    def test_solicitar_cash_out(self):
        self.carteira.depositar(Decimal('100.00'))
        with self.assertRaises(NotImplementedError):
            self.carteira.solicitar_cash_out(Decimal('50.00'))

    @skip('Foi implementado')
    def test_solicitar_cash_in(self):
        self.carteira.depositar(Decimal('100.00'))
        with self.assertRaises(NotImplementedError):
            self.carteira.solicitar_cash_in(Decimal('50.00'))


class UsuarioModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.permissoes = PermissoesNotificacao.objects.create(sms=True, email=True)
        cls.endereco = Endereco.objects.create(
            cep='01234567', estado='SP', cidade='São Paulo', bairro='Bela Vista', rua='Av Paulista', numero='123',
        )
        cls.usuario = Usuario.objects.create(
            id=uuid.uuid4(), email='johndoe@example.com', cpf='12345678901', nome='John Doe',
            data_nascimento='2000-01-01', telefone='11999999999', endereco=cls.endereco,
            permissoes=cls.permissoes
        )
        cls.usuario.carteira.depositar(Decimal('100.00'))

    def test_email_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            _ = Usuario.objects.create(
                id=uuid.uuid4(), email='johndoe@example.com', cpf='10987654321', nome='Jane Doe',
                data_nascimento='2000-01-01', telefone='11988888888', endereco=self.endereco,
                permissoes=self.permissoes
            )

    def test_cpf_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            _ = Usuario.objects.create(
                id=uuid.uuid4(), email='janedoe1@example.com', cpf='12345678901', nome='Jane Doe',
                data_nascimento='2000-01-01', telefone='11988888888', endereco=self.endereco,
                permissoes=self.permissoes
            )

    def test_envio_notificacao_valido(self):
        self.assertTrue(self.usuario.envioNotificacaoValido('sms'))
        self.assertTrue(self.usuario.envioNotificacaoValido('email'))
        self.assertFalse(self.usuario.envioNotificacaoValido('push'))

    def test_cpf_formatado(self):
        self.assertEqual(self.usuario.cpf_formatado, '123.456.789-01')

    def test_cpf_mascarado(self):
        self.assertEqual(self.usuario.cpf_marcarado, '***.456.789-**')

    def test_telefone_formatado(self):
        self.assertEqual(self.usuario.telefone_formatado, '(11) 99999-9999')

    def test_nome_formatado(self):
        self.assertEqual(self.usuario.nome_formatado, 'John Doe')

    def test_saldo(self):
        self.assertEqual(self.usuario.saldo, Decimal('100.00'))
