import os
from secrets import token_hex


def get_taxa_banca():
    return float(os.getenv('TAXA_BANCA'))


def gerar_codigo():
    return token_hex(8).upper()
