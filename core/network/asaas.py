from ast import Dict
from ctypes import Union
from decimal import Decimal
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import requests
from traitlets import Any


class Customer:

    @classmethod
    def create_custormer(cls, name: str, cpf: str, carteira_id: str, **kwargs) -> Union[bool, Dict[str, Any]]:
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

        response = requests.delete(url, headers=headers)
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
