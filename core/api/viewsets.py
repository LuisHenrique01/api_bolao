import os
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core import STATUS_HISTORICO
from core.mixins import WebhookActionMixin

from usuario.models import Carteira
from core.models import HistoricoTransacao
from core.network.asaas import Cobranca


class PaymentsWebhook(WebhookActionMixin, APIView):
    permission_classes = [AllowAny, ]

    def payment_received(self):
        try:
            transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                id=self.request.data['payment']['externalReference'])
        except ObjectDoesNotExist:
            transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                asaas_infos__asaas_id=self.request.data['payment']['id'])
        if transacao.status == STATUS_HISTORICO['PENDING']:
            transacao.carteira.depositar(valor=Decimal(self.request.data['payment']['value']),
                                         externo=True, is_webhook=True)
            transacao.status = STATUS_HISTORICO['CONFIRMED']
            transacao.save()
        try:
            carteira_banca = Carteira.objects.get(id=os.getenv('ID_CARTEIRA_BANCA'))
            valor = Decimal(self.request.data['payment']['value']) - Decimal(self.request.data['payment']['netValue'])
            carteira_banca.saque(valor=valor, externo=True, is_webhook=True)
            HistoricoTransacao.objects.create(status=STATUS_HISTORICO['CONFIRMED'], carteira=carteira_banca,
                                              valor=valor, externo=True,
                                              tipo=HistoricoTransacao.get_type(valor=-valor, externo=True),
                                              asaas_infos=transacao.asaas_infos)
        except ObjectDoesNotExist:
            pass
        return status.HTTP_200_OK

    def payment_overdue(self):
        try:
            transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                id=self.request.data['payment']['externalReference'])
        except ObjectDoesNotExist:
            transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                asaas_infos__asaas_id=self.request.data['payment']['id'])
        if transacao.status == STATUS_HISTORICO['PENDING']:
            _status = Cobranca.delete_cobranca(self.request.data['payment']['id'])
            if _status:
                transacao.status = STATUS_HISTORICO['REMOVED']
                transacao.save()
        return status.HTTP_200_OK


class TransfersWebhook(WebhookActionMixin, APIView):
    permission_classes = [AllowAny, ]

    def transfer_failed(self):
        try:
            transacao = HistoricoTransacao.objects.select_related('carteira').get(
                asaas_infos__asaas_id=self.request.data['transfer']['id']
            )
        except ObjectDoesNotExist:
            return status.HTTP_200_OK
        transacao.carteira.depositar(valor=self.request.data['transfer']['value'],
                                     externo=True, is_webhook=True)
        transacao.status = STATUS_HISTORICO['FAILED']
        transacao.save()
        return status.HTTP_200_OK

    def transfer_done(self):
        try:
            transacao = HistoricoTransacao.objects.select_related('carteira').get(
                asaas_infos__asaas_id=self.request.data['transfer']['id']
            )
        except ObjectDoesNotExist:
            return status.HTTP_200_OK
        transacao.status = STATUS_HISTORICO['CONFIRMED']
        transacao.save()
        return status.HTTP_200_OK
