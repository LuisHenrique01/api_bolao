import os
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from usuario.models import Carteira
from core.models import HistoricoTransacao


class PaymentsWebhook(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        request
        if request.data['event'] == 'PAYMENT_RECEIVED':
            try:
                transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                    id=request.data['payment']['externalReference'])
            except ObjectDoesNotExist:
                transacao = HistoricoTransacao.objects.select_related('carteira', 'asaas_infos').get(
                    asaas_infos__billing_id=request.data['payment']['id'])
            if transacao.status == 'PENDING':
                transacao.carteira.depositar(valor=Decimal(request.data['payment']['value']),
                                            externo=True, is_webhook=True)
                transacao.status = 'CONFIRMED'
                transacao.save()
            try:
                carteira_banca = Carteira.objects.get(id=os.getenv('ID_CARTEIRA_BANCA'))
                valor = Decimal(request.data['payment']['value']) - Decimal(request.data['payment']['netValue'])
                carteira_banca.saque(valor=valor, externo=True,
                                     is_webhook=True)
                HistoricoTransacao.objects.create(status='CONFIRMED', carteira=carteira_banca, valor=valor, externo=True, 
                                                  tipo=HistoricoTransacao.get_type(valor=-valor, externo=True),
                                                  asaas_infos=transacao.asaas_infos)
            except ObjectDoesNotExist:
                pass
        return Response(status.HTTP_200_OK)
        