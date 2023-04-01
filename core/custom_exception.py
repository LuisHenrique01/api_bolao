
class BaseException(Exception):

    @property
    def serializer(self):
        return {
            'message': getattr(self, 'message', 'Problema interno.')
        }


class SaldoInvalidoException(BaseException):

    def __init__(self, message="Saldo inválido."):
        self.message = message
        super().__init__(self.message)


class DepositoInvalidoException(BaseException):

    def __init__(self, message="Depósito inválido."):
        self.message = message
        super().__init__(self.message)


class UsuarioNaoEncontrado(BaseException):

    def __init__(self, message="Usuário não encontrado.") -> None:
        self.message = message
        super().__init__(self.message)
