# Generated by Django 4.2.4 on 2024-09-11 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0007_alter_movimientos_idcierre'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionParametros',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('codigo', models.CharField(max_length=10)),
                ('nombre', models.CharField(max_length=100)),
                ('valor', models.CharField(max_length=100)),
                ('tipo_valor', models.CharField(max_length=1)),
                ('descripcion', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name_plural': 'Configuracion Parametros',
                'ordering': ['-id'],
            },
        ),
        migrations.AlterModelOptions(
            name='movimientos',
            options={'ordering': ['-fecha', '-id'], 'verbose_name': 'Movimiento', 'verbose_name_plural': 'Movimientos'},
        ),
    ]