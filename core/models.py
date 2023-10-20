from decimal import Decimal
from uuid import uuid4
from django.db import models

from core.network.asaas import Cobranca

from . import TIPO_CHOICES, STATUS_HISTORICO


class BaseModel(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        abstract = True


class AsaasInformations(BaseModel):

    billing_id = models.CharField("Cobrança ID", max_length=50, blank=True, null=True)
    due_date = models.DateField("Data de vencimento", blank=True, null=True)
    value = models.DecimalField('Valor', max_digits=9, decimal_places=2)
    net_value = models.DecimalField('Valor efetivo', max_digits=9, decimal_places=2)
    invoice_url = models.CharField("URL da cobrança", max_length=150, blank=True, null=True)
    billet_url = models.CharField("URL do boleto", max_length=150, blank=True, null=True)

    def get_pix_infos(self) -> dict:
        status, infos = Cobranca.get_pix(self.billing_id)
        if status:
            return infos
        return {
            "encodedImage": None,
            "payload": None,
            "expirationDate": None
        }

    def __str__(self) -> str:
        return self.billing_id


class HistoricoTransacao(BaseModel):

    status = models.CharField('Status', max_length=10, choices=STATUS_HISTORICO.items(), default='CONFIRMED')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES.items())
    valor = models.DecimalField('Valor', max_digits=9, decimal_places=2)
    carteira = models.ForeignKey('usuario.Carteira', on_delete=models.CASCADE, related_name='historico_transacao')
    externo = models.BooleanField('Transação externa', default=False)
    pix = models.CharField("PIX", max_length=50, blank=True, null=True)
    asaas_infos = models.ForeignKey(AsaasInformations, on_delete=models.CASCADE,
                                    related_name='historico_transacao', blank=True, null=True)

    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Histórico transações'

    @classmethod
    def get_type(cls, valor: Decimal, externo: bool):
        if externo and valor > 0:
            return 'DEPOSITO'
        elif externo and valor < 0:
            return 'SAQUE'
        elif valor < 0:
            return 'COMPRA'
        else:
            return 'GANHO'
    
    def __str__(self) -> str:
        return f'{self.tipo} - {self.status} => {self.valor}'
