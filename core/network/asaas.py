import os
from typing import Union, Dict, Any
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
import requests
from core.utils import clean_cpf


class Customer:

    @classmethod
    def create_customer(cls, name: str, cpf: str, carteira_id: str, **kwargs) -> Union[bool, Dict[str, Any]]:
        """Criar um cliente na Asaas."""
        url = os.getenv('URL_ASAAS') + 'customers'
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": os.getenv('ASAAS_KEY')
        }
        payload = {
            "name": name,
            "cpfCnpj": cpf,
            "externalReference": carteira_id,
            "notificationDisabled": True,
        }
        if kwargs:
            payload.update(kwargs)

        response = requests.post(url=url, headers=headers, json=payload, timeout=40)
        return response.status_code == 200, response.json()

    @classmethod
    def delete_custormer(cls, customer_id: str) -> bool:
        url = os.getenv('URL_ASAAS') + 'customers/' + customer_id
        headers = {
            "accept": "application/json",
            "access_token": os.getenv('ASAAS_KEY')
        }

        response = requests.delete(url, headers=headers, timeout=40)
        return response.status_code == 200


class Cobranca:

    @classmethod
    def gerar_cobranca(cls, customer_id: str, valor: Union[float, Decimal],
                       transaction_id: str = None) -> Union[bool, Dict[str, Any]]:
        url = os.getenv('URL_ASAAS') + 'payments'
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": os.getenv('ASAAS_KEY')
        }
        payload = {
            "billingType": "PIX",
            "customer": customer_id,
            "value": round(float(valor), 2),
            "dueDate": (date.today() + relativedelta(days=1)).strftime('%Y-%m-%d'),
            "externalReference": transaction_id
        }
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        return response.status_code == 200, response.json()

    @classmethod
    def get_pix(cls, billet_id: str) -> Union[bool, Dict[str, Any]]:
        url = os.getenv('URL_ASAAS') + 'payments/' + billet_id + '/pixQrCode'
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": os.getenv('ASAAS_KEY')
        }
        response = requests.get(url, headers=headers, timeout=40)
        return response.status_code == 200, response.json()

    @classmethod
    def delete_cobranca(cls, payment_id: str) -> bool:
        url = os.getenv('URL_ASAAS') + 'payments/' + payment_id
        headers = {
            "accept": "application/json",
            "access_token": os.getenv('ASAAS_KEY')
        }

        response = requests.delete(url, headers=headers, timeout=40)
        return response.status_code == 200


class Transferencia:

    @classmethod
    def enviar_pix(cls, valor: Decimal, usuario, banco_code: str, agencia: str,
                   tipo_conta: str, numero_conta: str, digito_conta: str):
        url = os.getenv('URL_ASAAS') + 'transfers'
        payload = {
            "bankAccount": {
                "bank": {"code": banco_code},
                "ownerBirthDate": usuario.data_nascimento.strftime('%Y-%m-%d'),
                "ownerName": usuario.nome,
                "agency": agencia,
                "bankAccountType": tipo_conta,
                "cpfCnpj": clean_cpf(usuario.cpf),
                "accountDigit": digito_conta,
                "account": numero_conta
            },
            "operationType": "PIX",
            "value": round(float(valor), 2)
            }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": os.getenv('ASAAS_KEY')
        }
        response = requests.post(url=url, headers=headers, json=payload, timeout=40)
        return response.status_code == 200, response.json()

    @classmethod
    def buscar_tranferencia(cls, transferencia_id: str):
        url = os.getenv('URL_ASAAS') + "transfers/" + transferencia_id
        headers = {
            "accept": "application/json",
            "access_token": os.getenv('ASAAS_KEY')
        }
        response = requests.get(url, headers=headers)
        return response.status_code == 200, response.json()
