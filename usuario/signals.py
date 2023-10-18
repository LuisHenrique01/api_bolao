from django.db.models.signals import post_save
from django.dispatch import receiver
from core.network.asaas import Customer
from core.utils import clean_cpf
from .models import Carteira, Usuario


@receiver(post_save, sender=Usuario)
def create_carteira(sender, usuario: Usuario, **kwargs):
    if not usuario.carteira:
        carteira = Carteira.objects.create()
        usuario.carteira = carteira
        status, customer = Customer.create_custormer(usuario.name, clean_cpf(usuario.cpf), carteira.id)
        if status:
            carteira.asaas_customer = customer["id"]
        usuario.bloqueado = not status
        carteira.save()
        usuario.save()
