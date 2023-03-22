from decimal import Decimal
from uuid import uuid4
from django.db import models

from . import TIPO_CHOICES


class BaseModel(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        abstract = True


class HistoricoTransacao(BaseModel):

    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES.items())
    valor = models.DecimalField('Valor', max_digits=9, decimal_places=2)
    carteira = models.ForeignKey('usuario.Carteira', on_delete=models.CASCADE, related_name='historico_transacao')
    externo = models.BooleanField('Transação externa', default=False)
    pix = models.CharField("PIX", max_length=50, blank=True, null=True)

    @classmethod
    def criar_registro(cls, carteira, valor: Decimal, externo: bool, pix: str = None):
        if externo and valor > 0:
            tipo = 'DEPOSITO'
        elif externo and valor < 0:
            tipo = 'SAQUE'
        elif valor < 0:
            tipo = 'COMPRA'
        else:
            tipo = 'GANHO'
        instance = cls(tipo=tipo, carteira=carteira, valor=valor, externo=externo, pix=pix)
        instance.save()
