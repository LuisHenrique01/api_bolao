# Generated by Django 4.1.7 on 2023-03-13 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bolao', '0002_alter_campeonato_options_alter_campeonato_id_externo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jogo',
            name='id_externo',
            field=models.CharField(max_length=50, unique=True, verbose_name='ID externo'),
        ),
        migrations.AlterField(
            model_name='time',
            name='id_externo',
            field=models.CharField(max_length=50, unique=True, verbose_name='ID externo'),
        ),
    ]
