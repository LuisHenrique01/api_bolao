from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PermissoesNotificacao, Endereco, Usuario


admin.site.register(PermissoesNotificacao)
admin.site.register(Endereco)


class UsuarioAdmin(UserAdmin):
    fields = ['nome', 'email',   'telefone', 'is_active', 'permissoes', 'endereco']
    fieldsets = None
    list_display = ['nome_formatado', 'email', 'cpf_marcarado', 'telefone_formatado',
                    'saldo', 'permissoes']
    ordering = ['nome']
    list_filter = ['permissoes']
    search_fields = ['nome', 'saldo', 'email', 'cpf_marcarado']

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


admin.site.register(Usuario, UsuarioAdmin)
