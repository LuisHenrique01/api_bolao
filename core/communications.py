import os
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from datetime import datetime, timedelta


class Email:

    @classmethod
    def recuperar_senha(cls, email: str, codigo: str, username: str = None):
        titulo = "Código para recuperação de senha"
        expiracao = datetime.now() + timedelta(hours=2)
        expiracao_str = expiracao.strftime('%H:%M')
        sender = EmailMessage(
            subject=titulo,
            body=render_to_string('email/recuperacao.html', {'codigo': codigo, 'expiracao': expiracao_str,
                                                             'username': username or 'usuário'}),
            from_email=os.getenv('EMAIL'),
            to=[email],
        )
        sender.content_subtype = "html"
        sender.send(fail_silently=False)

    @classmethod
    def validar_usuario(cls, email: str, codigo: str, username: str = None):
        titulo = "Validação da Conta Starbet.space"
        expiracao = datetime.now() + timedelta(hours=2)
        expiracao_str = expiracao.strftime('%H:%M')
        sender = EmailMessage(
            subject=titulo,
            body=render_to_string('email/validacao.html', {'codigo': codigo, 'expiracao': expiracao_str,
                                                           'username': username or 'usuário'}),
            from_email=os.getenv('EMAIL'),
            to=[email],
        )
        sender.content_subtype = "html"
        sender.send(fail_silently=False)
