import os
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core import STATUS_HISTORICO

from usuario.models import Carteira
from core.models import HistoricoTransacao
from core.network.asaas import Cobranca


class PaymentsWebhook(APIView):
    permission_classes = [AllowAny, ]

    def payment_received(self):
        try:
            transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                id=self.request.data['payment']['externalReference'])
        except ObjectDoesNotExist:
            transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                asaas_infos__billing_id=self.request.data['payment']['id'])
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
                asaas_infos__billing_id=self.request.data['payment']['id'])
        if transacao.status == STATUS_HISTORICO['PENDING']:
            _status = Cobranca.delete_cobranca(self.request.data['payment']['id'])
            if _status:
                transacao.status = STATUS_HISTORICO['REMOVED']
                transacao.save()
        return status.HTTP_200_OK

    def post(self, request, *args, **kwargs):
        default_function = lambda: status.HTTP_200_OK
        event = request.data['event']
        handler = getattr(self, event.lower(), default_function)
        _status = handler()
        return Response(status=_status)


class TransfersWebhook(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        default_function = lambda: status.HTTP_200_OK
        event = request.data['event']
        handler = getattr(self, event.lower(), default_function)
        _status = handler()
        return Response(status=_status)