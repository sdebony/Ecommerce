# Generated by Django 4.2.4 on 2023-09-21 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_accountdirecciones_dir_correo'),
    ]

    operations = [
        migrations.AddField(
            model_name='permition',
            name='orden',
            field=models.IntegerField(default=0),
        ),
    ]