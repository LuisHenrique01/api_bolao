import os
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from datetime import datetime, timedelta


class Email:

    @classmethod
    def recuperar_senha(cls, email: str, codigo: str):
        titulo = "Código para recuperação de senha"
        mensagem = "Siga as instruções da plataforma para recuperar sua senha."
        expiracao = datetime.now() + timedelta(hours=2)
        expiracao_str = expiracao.strftime('%H:%M')
        sender = EmailMessage(
            subject=titulo,
            body=render_to_string('email/recuperacao.html', {'titulo': titulo, 'codigo': codigo,
                                                             'mensagem': mensagem, 'expiracao': expiracao_str}),
            from_email=os.getenv('EMAIL'),
            to=[email],
        )
        sender.content_subtype = "html"
        sender.send(fail_silently=False)

    def validar_usuario(cls, email: str, codigo: str):
        titulo = "Código para validar sua conta"
        mensagem = "Siga as instruções da plataforma para validar sua conta."
        expiracao = datetime.now() + timedelta(hours=2)
        expiracao_str = expiracao.strftime('%H:%M')
        sender = EmailMessage(
            subject=titulo,
            body=render_to_string('email/validacao.html', {'titulo': titulo, 'codigo': codigo,
                                                           'mensagem': mensagem, 'expiracao': expiracao_str}),
            from_email=os.getenv('EMAIL'),
            to=[email],
        )
        sender.content_subtype = "html"
        sender.send(fail_silently=False)
