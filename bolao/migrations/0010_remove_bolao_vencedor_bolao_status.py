# Generated by Django 4.1.7 on 2023-03-17 03:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bolao', '0009_alter_bolao_taxa_criador'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bolao',
            name='vencedor',
        ),
        migrations.AddField(
            model_name='bolao',
            name='status',
            field=models.CharField(choices=[('ATIVO', 'ATIVO'), ('PALPITES PAUSADOS', 'PALPITES PAUSADOS'), ('JOGO INICIADO', 'JOGO INICIADO'), ('FINALIZADO', 'FINALIZADO'), ('CANCELADO', 'CANCELADO')], default='ATIVO', max_length=20),
        ),
    ]
