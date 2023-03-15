import os
from secrets import token_hex


def get_taxa_banca() -> float:
    """Busca nas variáveis de ambiente a taxa da banca."""
    return float(os.getenv('TAXA_BANCA'))


def gerar_codigo() -> str:
    """Gera um token aleatório."""
    return token_hex(8).upper()


def valida_cpf(cpf: str) -> bool:
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
    else:
        return False
