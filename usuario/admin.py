from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import PermissoesNotificacao, Endereco, Usuario

admin.site.register(PermissoesNotificacao)
admin.site.register(Endereco)


class UsuarioAdmin(UserAdmin):
    fields = ['nome', 'email',   'telefone', 'is_active', 'permissoes', 'endereco']
    fieldsets = None
    list_display = ['nome_formatado', 'email', 'cpf_marcarado', 'telefone_formatado',
                    'saldo', 'permissoes', 'bloqueado']
    ordering = ['nome']
    list_filter = ['permissoes']
    search_fields = ['nome', 'saldo', 'email', 'cpf_marcarado']
    actions = ['bloquear_usuario']

    @admin.display(description='Nome')
    def nome_formatado(self, obj: Usuario):
        return obj.nome_formatado

    @admin.display(description="CPF")
    def cpf_marcarado(self, obj: Usuario):
        return obj.cpf_marcarado

    @admin.display(description="Telefone")
    def telefone_formatado(self, obj: Usuario):
        return obj.telefone_formatado

    @admin.display(description="Saldo")
    def saldo(self, obj: Usuario):
        return obj.saldo

    @admin.display(description="Bloqueado")
    def bloqueado(self, obj: Usuario):
        return obj.carteira.bloqueado

    def bloquear_usuario(self, request, queryset):
        if getattr(request.user, 'is_superuser', False):
            for usuario in queryset:
                usuario.carteira.bloqueado = True
                usuario.carteira.save()
            messages.success(request, "Usuário(s) bloqueado(s) com sucesso.")
            return
        messages.error(request, "Você não tem permissão para realizar essa operação.")


admin.site.register(Usuario, UsuarioAdmin)
