import os
from secrets import token_hex
from decimal import Decimal


def get_taxa_banca():
    return Decimal(os.getenv('TAXA_BANCA'))


def gerar_codigo():
    return token_hex(8).upper()