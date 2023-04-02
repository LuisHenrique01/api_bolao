from rest_framework.permissions import BasePermission


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
