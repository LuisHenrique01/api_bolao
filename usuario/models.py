import os
from decimal import Decimal
from uuid import uuid4
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin

from django.db import models

from core.custom_exception import SaldoInvalidoException, DepositoInvalidoException
from core.models import BaseModel

from .managers import UserManager


class PermissoesNotificacao(BaseModel):

    sms = models.BooleanField('SMS', default=True)
    email = models.BooleanField('E-mail', default=True)

    class Meta:
        verbose_name = "Pemissão para notificação"
        verbose_name_plural = "Pemissões para notificações"

    def __str__(self):
        return f'SMS: {self.sms}|E-mail: {self.email}'


class Endereco(BaseModel):

    cep = models.CharField('CEP', max_length=9)
    estado = models.CharField('Estado', max_length=25)
    cidade = models.CharField('Cidade', max_length=75)
    bairro = models.CharField('Bairro', max_length=25)
    rua = models.CharField('Rua', max_length=75, blank=True, null=True)
    numero = models.CharField('Número', max_length=15, blank=True, null=True)
    complemento = models.CharField('Complemento', max_length=75, blank=True, null=True)

    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"

    def __str__(self):
        return f'CEP: {self.cep}|Cidade: {self.cidade}'


class Carteira(BaseModel):

    __saldo = models.DecimalField('Saldo', name='saldo', max_digits=9, decimal_places=2, default=Decimal(0))

    def saque_valido(self, valor: Decimal) -> bool:
        return valor >= Decimal(os.getenv('MIN_SAQUE')) and (self.saldo - valor) >= 0

    @classmethod
    def deposito_valido(self, valor: Decimal) -> bool:
        return valor >= Decimal(os.getenv('MIN_DEPOSITO'))

    def saque(self, valor: Decimal):
        if not self.saque_valido(valor):
            raise SaldoInvalidoException()
        self.__saldo -= valor

    def depositar(self, valor: Decimal):
        if not self.deposito_valido(valor):
            raise DepositoInvalidoException()
        self.__saldo += valor

    @property
    def saldo(self):
        return self.__saldo

    def transferir(self, valor: Decimal) -> bool:
        raise NotImplementedError(f'Transferência de {valor} R$ não for realizada.')

    def __str__(self):
        try:
            return f'{self.usuario}|Saldo: {self.saldo}'
        except Exception:
            return f'Saldo: {self.saldo}'


class Usuario(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField('E-mail', unique=True)
    cpf = models.CharField('CPF', max_length=14, unique=True, editable=False)
    nome = models.CharField('Nome', max_length=150)
    data_nascimento = models.DateField('Data de nascimento')
    telefone = models.CharField('Telefone', max_length=11)
    endereco = models.ForeignKey(Endereco, on_delete=models.SET_NULL, null=True, related_name='usuarios')
    permissoes = models.ForeignKey(PermissoesNotificacao, on_delete=models.SET_NULL, null=True, related_name='usuarios')
    carteira = models.OneToOneField(Carteira, on_delete=models.CASCADE)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['cpf', 'nome', 'data_nascimento', 'telefone', 'carteira']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def envioNotificacaoValido(self, tipo: str) -> bool:
        return getattr(self.permissoes, tipo, False)

    @property
    def cpf(self):
        return f'{self.cpf[:3:]}.{self.cpf[3:6:]}.{self.cpf[6:9:]}-{self.cpf[9::]}'

    @property
    def telefone(self):
        return f'({self.telefone[:2:]}) {self.telefone[2:7:]}-{self.telefone[7::]}'

    def __str__(self) -> str:
        _nome = self.nome.split()
        return f'{_nome[0]} {_nome[-1]}'
