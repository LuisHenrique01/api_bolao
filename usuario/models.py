import os
from decimal import Decimal
from uuid import uuid4
from datetime import date
from datetime import timedelta
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin

from django.db import models, transaction
from django.utils import timezone
from core import TIPO_CONTA, STATUS_HISTORICO

from core.custom_exception import SaldoInvalidoException, DepositoInvalidoException, UnavailableService
from core.models import BaseModel, HistoricoTransacao, AsaasInformations
from core.utils import clean_cpf, cpf_valido, gerar_codigo
from core.network.asaas import Cobranca, Customer, Transferencia

from .managers import UserManager


class PermissoesNotificacao(BaseModel):

    sms = models.BooleanField('SMS', default=True)
    email = models.BooleanField('E-mail', default=True)
    sms_verificado = models.BooleanField('SMS vefiricado', default=False)
    email_verificado = models.BooleanField('E-mail verificado', default=False)

    def criar_codigo(self, tipo: str):
        codigo = CodigosDeValidacao(permissao=self, tipo=tipo)
        codigo.save()
        return codigo

    class Meta:
        verbose_name = "Pemissão para notificação"
        verbose_name_plural = "Pemissões para notificações"

    def __str__(self) -> str:
        return f'SMS: {self.sms}|E-mail: {self.email}'


class CodigosDeValidacao(BaseModel):

    permissao = models.ForeignKey(PermissoesNotificacao, verbose_name='Permissão',
                                  on_delete=models.CASCADE, related_name='codigos')
    tipo = models.CharField('Tipo', max_length=50)
    codigo = models.CharField('Código', max_length=50, blank=True)
    confirmado = models.BooleanField('Confirmado', default=False)

    @classmethod
    def valido(self, codigo: str) -> bool:
        now = timezone.now() - timedelta(hours=2)
        return CodigosDeValidacao.objects.filter(codigo=codigo, created_at__gte=now).exists()

    def save(self, **kwargs) -> None:
        if self._state.adding:
            self.codigo = gerar_codigo(numerico=True)
        return super().save(**kwargs)

    class Meta:
        verbose_name = "Código de validação"
        verbose_name_plural = "Códigos de validação"

    def __str__(self) -> str:
        return f'Código: {self.codigo}|Confirmado: {self.confirmado}'


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

    def __str__(self) -> str:
        return f'CEP: {self.cep}|Cidade: {self.cidade}'


class ContaExternaUsuario(BaseModel):

    carteira = models.ForeignKey('usuario.Carteira', verbose_name="Carteira", on_delete=models.CASCADE,
                                 related_name='conta_externa')
    code_banco = models.CharField("Código bancario", max_length=5)
    agencia = models.CharField("Agencia", max_length=5)
    tipo_conta = models.CharField("Tipo de conta", max_length=20, choices=TIPO_CONTA.items())
    num_conta = models.CharField("Conta", max_length=15)
    digito = models.CharField("Digito", max_length=5)

    class Meta:
        verbose_name = 'Conta externa'
        verbose_name_plural = 'Contas externa'

    def __str__(self) -> str:
        return f'{self.code_banco} - {self.num_conta}'


class Carteira(BaseModel):

    _saldo = models.DecimalField('Saldo', name='saldo', max_digits=9, decimal_places=2, default=Decimal(0))
    bloqueado = models.BooleanField('Carteira bloqueada', default=False)
    asaas_customer = models.CharField("Asaas CustomerID", max_length=50, blank=True, null=True)

    def saque_valido(self, valor: Decimal, externo: bool = False) -> bool:
        if self.bloqueado:
            return False
        if externo:
            return valor >= Decimal(os.getenv('MIN_SAQUE')) and (self.saldo - valor) >= 0
        return (self.saldo - valor) >= 0

    def deposito_valido(self, valor: Decimal, externo: bool = False) -> bool:
        if self.bloqueado:
            return False
        if externo:
            return valor >= Decimal(os.getenv('MIN_DEPOSITO'))
        return valor >= 0

    @transaction.atomic
    def saque(self, valor: Decimal, externo: bool = False, salvar_historico: bool = True) -> None:
        if not self.saque_valido(valor, externo=externo) and salvar_historico:
            raise SaldoInvalidoException()
        self.saldo -= valor
        self.save()
        if salvar_historico:
            HistoricoTransacao.objects.create(carteira=self, valor=valor, externo=externo,
                                              tipo=HistoricoTransacao.get_type(valor=-valor, externo=externo))

    @transaction.atomic
    def depositar(self, valor: Decimal, externo: bool = False, is_webhook: bool = False) -> None:
        if not self.deposito_valido(valor, externo=externo) and not is_webhook:
            raise DepositoInvalidoException()
        self.saldo += valor
        self.save()
        if not is_webhook:
            HistoricoTransacao.objects.create(carteira=self, valor=valor, externo=externo,
                                              tipo=HistoricoTransacao.get_type(valor=valor, externo=externo))

    @property
    def saldo(self):
        return self.saldo

    def solicitar_cash_in(self, valor: Decimal) -> HistoricoTransacao:
        if self.deposito_valido(valor, externo=True):
            uuid = uuid4()
            status, response = Cobranca.gerar_cobranca(customer_id=self.asaas_customer, valor=valor,
                                                       transaction_id=str(uuid))
            if status:
                asaas_infos = AsaasInformations.objects.create(asaas_id=response['id'],
                                                               due_date=date.fromisoformat(response['dueDate']),
                                                               value=response['value'],
                                                               net_value=response['netValue'],
                                                               invoice_url=response['invoiceUrl'],
                                                               billet_url=response['bankSlipUrl'])
                transaction = HistoricoTransacao.objects.create(id=uuid, carteira=self, valor=valor,
                                                                externo=True, status='PENDING',
                                                                tipo=HistoricoTransacao.get_type(valor=valor,
                                                                                                 externo=True),
                                                                asaas_infos=asaas_infos)
                return transaction
            raise UnavailableService()
        raise DepositoInvalidoException()

    def solicitar_cash_out(self, valor: Decimal, conta: dict) -> bool:
        if self.saque_valido(valor, externo=True):
            status, response = Transferencia.enviar_pix(valor=valor, banco_code=conta['code_banco'],
                                                        agencia=conta['agencia'], numero_conta=conta['num_conta'],
                                                        digito_conta=conta['digito'], tipo_conta=conta['tipo_conta'],
                                                        usuario=self.usuario)
            if status:
                self.saque(valor=valor, externo=True, salvar_historico=False)
                obj_conta, _ = ContaExternaUsuario.objects.get_or_create(**conta, defaults={'carteira': self})
                asaas_infos = AsaasInformations.objects.create(asaas_id=response['id'], op_type=response['object'],
                                                               value=response['value'], net_value=response['netValue'])
                HistoricoTransacao.objects.create(carteira=self, valor=-valor, externo=True, conta=obj_conta,
                                                  tipo=HistoricoTransacao.get_type(valor=-valor, externo=True),
                                                  status=STATUS_HISTORICO['PENDING'],
                                                  asaas_infos=asaas_infos)
                return True
            return UnavailableService()
        raise SaldoInvalidoException()

    def __str__(self):
        try:
            return f'{self.usuario}|Saldo: {self.saldo}'
        except Exception:
            return f'Saldo: {self.saldo}'


class Usuario(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField('E-mail', unique=True)
    cpf = models.CharField('CPF', max_length=14, unique=True, validators=[cpf_valido])
    nome = models.CharField('Nome', max_length=150)
    data_nascimento = models.DateField('Data de nascimento')
    telefone = models.CharField('Telefone', max_length=11)
    endereco = models.ForeignKey(Endereco, on_delete=models.SET_NULL, null=True, related_name='usuarios')
    permissoes = models.OneToOneField(PermissoesNotificacao, on_delete=models.SET_NULL,
                                      null=True, related_name='usuario')
    carteira = models.OneToOneField(Carteira, on_delete=models.CASCADE, blank=True, related_name='usuario')

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['cpf', 'nome', 'data_nascimento', 'telefone', 'carteira']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def envioNotificacaoValido(self, tipo: str) -> bool:
        return getattr(self.permissoes, tipo, False)

    @property
    def cpf_formatado(self) -> str:
        return f'{self.cpf[:3:]}.{self.cpf[3:6:]}.{self.cpf[6:9:]}-{self.cpf[9::]}'

    @property
    def cpf_marcarado(self) -> str:
        return f'***.{self.cpf[3:6:]}.{self.cpf[6:9:]}-**'

    @property
    def telefone_formatado(self) -> str:
        return f'({self.telefone[:2:]}) {self.telefone[2:7:]}-{self.telefone[7::]}'

    @property
    def nome_formatado(self) -> str:
        _nome = self.nome.split()
        return f'{_nome[0]} {_nome[-1]}'

    @property
    def saldo(self) -> str:
        return self.carteira.saldo

    def save(self, **kwargs):
        if self._state.adding:
            self.carteira = Carteira.objects.create()
            status, customer = Customer.create_customer(self.nome, clean_cpf(self.cpf),
                                                        str(self.carteira.id))
            if status:
                self.carteira.asaas_customer = customer["id"]
                self.carteira.save()
            self.set_password(self.password)
        return super().save(**kwargs)

    def __str__(self) -> str:
        _nome = self.nome.split()
        return f'{_nome[0]} {_nome[-1]}'
