# Generated by Django 4.2.4 on 2023-10-14 23:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cierres',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('mes', models.BigIntegerField()),
                ('ano', models.BigIntegerField()),
                ('total_ultimo_cierre', models.FloatField(default=0)),
                ('total_movimientos_registrados', models.FloatField(default=0)),
                ('total_saldo_real', models.FloatField(default=0)),
                ('total_diferencia', models.FloatField(default=0)),
                ('observaciones', models.CharField(blank=True, default='', max_length=250)),
                ('cuenta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.cuentas')),
            ],
            options={
                'verbose_name_plural': 'Cierres',
                'ordering': ['-fecha', '-id'],
            },
        ),
        migrations.AddField(
            model_name='movimientos',
            name='idcierre',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contabilidad.cierres'),
        ),
    ]