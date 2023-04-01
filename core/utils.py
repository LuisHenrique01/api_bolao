import os
import re
from secrets import token_hex, randbelow
from django.core.exceptions import ValidationError


def get_taxa_banca() -> float:
    """Busca nas variáveis de ambiente a taxa da banca."""
    return float(os.getenv('TAXA_BANCA'))


def gerar_codigo(numerico: bool = False) -> str:
    """Gera um token aleatório."""
    if numerico:
        return ''.join((str(randbelow(9)) for _ in range(6)))
    return token_hex(3).upper()


def cpf_valido(cpf: str, raise_exception: bool = True) -> bool:
    """
    Valida um CPF, retornando True se for válido ou False caso contrário.

    :param cpf: CPF a ser validado.
    :return: True se CPF for válido, False caso contrário.
    """
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) != 11:
        return False

    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False

    # Cálculo do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito_1 = (soma * 10) % 11
    if digito_1 == 10:
        digito_1 = 0

    # Cálculo do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito_2 = (soma * 10) % 11
    if digito_2 == 10:
        digito_2 = 0

    # Verifica se os dígitos verificadores estão corretos
    if cpf[-2:] == f'{digito_1}{digito_2}':
        return True

    if raise_exception:
        raise ValidationError(f"O CPF {cpf} inválido.")

    return False


def formato_cpf_valido(cpf: str) -> bool:
    if re.match(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        return True
    return False


def formato_telefone_valido(telefone: str) -> bool:
    if re.match(r'^\([1-9]{2}\)(?:[2-8]|9[1-9])[0-9]{3}\-[0-9]{4}$', telefone):
        return True
    return False


def formato_email_valido(email: str) -> bool:
    if re.match(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', email):
        return True
    return False


def qual_tipo_chave_pix(chave_pix: str) -> str:

    chave_pix = chave_pix.replace(" ", "")

    if formato_email_valido(chave_pix):
        return "e-mail"

    if cpf_valido(chave_pix, raise_exception=False):
        return "CPF"

    if formato_telefone_valido(chave_pix) or \
       (chave_pix.isnumeric() and (len(chave_pix) == 10 or len(chave_pix) == 11)):
        return "telefone"

    if len(chave_pix) == 14 and chave_pix.isnumeric():
        return "CNPJ"

    if len(chave_pix) == 32 and chave_pix.isalnum():
        return "aleatorio"
