# Generated by Django 4.2.4 on 2024-09-19 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0016_comprasenc_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='comprasenc',
            name='id_pago',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]