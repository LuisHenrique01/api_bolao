# Generated by Django 4.1.7 on 2023-03-17 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bolao', '0007_rename_created_bolao_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bolao',
            name='vencedor',
            field=models.CharField(choices=[('ATIVO', 'ATIVO'), ('PALPITES PAUSADOS', 'PALPITES PAUSADOS'), ('JOGO INICIADO', 'JOGO INICIADO'), ('FINALIZADO', 'FINALIZADO')], default='ATIVO', max_length=20),
        ),
    ]
