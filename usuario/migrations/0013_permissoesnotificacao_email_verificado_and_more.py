# Generated by Django 4.1.7 on 2023-03-25 15:41

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0012_alter_usuario_carteira'),
    ]

    operations = [
        migrations.AddField(
            model_name='permissoesnotificacao',
            name='email_verificado',
            field=models.BooleanField(default=False, verbose_name='E-mail verificado'),
        ),
        migrations.AddField(
            model_name='permissoesnotificacao',
            name='sms_verificado',
            field=models.BooleanField(default=False, verbose_name='SMS vefiricado'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='permissoes',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios', to='usuario.permissoesnotificacao'),
        ),
        migrations.CreateModel(
            name='CodigosDeValidacao',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('tipo', models.CharField(max_length=50, verbose_name='Tipo')),
                ('codigo', models.CharField(blank=True, max_length=50, verbose_name='Código')),
                ('permissao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='codigos', to='usuario.permissoesnotificacao', verbose_name='Permissão')),
            ],
            options={
                'verbose_name': 'Código de validação',
                'verbose_name_plural': 'Códigos de validação',
            },
        ),
    ]
