# Generated by Django 4.1.7 on 2023-05-15 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bolao', '0013_alter_bilhete_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='bolao',
            name='bilhetes_minimos',
            field=models.PositiveIntegerField(default=0, verbose_name='Palpites mínimos'),
        ),
    ]
