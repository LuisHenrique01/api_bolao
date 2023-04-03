from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated


class UsuarioBloqueado(BasePermission):

    message = 'Seu usuário está bloqueado.'

    def has_permission(self, request, _):
        return bool(request.user and request.user.is_active)


class CarteiraBloqueada(BasePermission):

    message = 'Sua carteira está bloqueada.'

    def has_permission(self, request, _):
        return bool(request.user and not request.user.carteira.bloqueado)


class UsuarioValidado(BasePermission):

    message = 'Seu usuário não está verificado.'

    def has_permission(self, request, _):
        return bool(request.user and (request.user.permissoes.email_verificado or
                                      request.user.permissoes.sms_verificado))


class Leitura(BasePermission):

    def has_permission(self, request, _):
        return bool(request.method in SAFE_METHODS)


DEFAULT_PERMISSIONS = [UsuarioBloqueado, UsuarioValidado]
CARTEIRA_PERMISSIONS = [*DEFAULT_PERMISSIONS, IsAuthenticated, CarteiraBloqueada]
LEITURA_OU_AUTENTICACAO_COMPLETA = [UsuarioBloqueado & UsuarioValidado & IsAuthenticated | Leitura]