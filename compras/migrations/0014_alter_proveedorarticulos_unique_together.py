# Generated by Django 4.2.4 on 2024-09-13 00:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0013_alter_proveedorarticulos_id_product'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='proveedorarticulos',
            unique_together={('proveedor', 'codigo_prod_prov', 'unidad_medida', 'nombre_articulo')},
        ),
    ]