# Generated by Django 4.2.4 on 2023-12-28 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0002_cierres_movimientos_idcierre'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuentas',
            name='alias',
            field=models.CharField(default='', max_length=50, verbose_name='Alias'),
        ),
        migrations.AddField(
            model_name='cuentas',
            name='cbu',
            field=models.CharField(default='', max_length=25, verbose_name='CBU'),
        ),
        migrations.AddField(
            model_name='cuentas',
            name='cuil',
            field=models.CharField(default='', max_length=25, verbose_name='Cuil'),
        ),
        migrations.AddField(
            model_name='cuentas',
            name='documento',
            field=models.CharField(default='', max_length=25, verbose_name='Documento'),
        ),
        migrations.AddField(
            model_name='cuentas',
            name='nro_cuenta',
            field=models.CharField(default='', max_length=25, verbose_name='Nro Cuenta'),
        ),
    ]