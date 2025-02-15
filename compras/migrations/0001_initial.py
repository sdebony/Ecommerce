# Generated by Django 4.2.4 on 2025-01-02 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0001_initial'),
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Marcas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marca', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Marca',
                'verbose_name_plural': 'Marcas',
            },
        ),
        migrations.CreateModel(
            name='Proveedores',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('contacto', models.CharField(blank=True, max_length=100)),
                ('direccion', models.CharField(blank=True, max_length=100)),
                ('telefono1', models.CharField(blank=True, max_length=100)),
                ('telefono2', models.CharField(blank=True, max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('web', models.CharField(blank=True, max_length=100)),
                ('facebook', models.CharField(blank=True, max_length=100)),
                ('instragram', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'Proveedor',
                'verbose_name_plural': 'Proveedores',
            },
        ),
        migrations.CreateModel(
            name='UnidadMedida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=2, unique=True)),
                ('nombre', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'UnidadMedida',
                'verbose_name_plural': 'UnidadMedida',
            },
        ),
        migrations.CreateModel(
            name='ProveedorArticulos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_prod_prov', models.CharField(max_length=25)),
                ('nombre_articulo', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('cantidad_unidad_medida', models.FloatField(default=1)),
                ('precio_compra', models.FloatField(default=0)),
                ('precio_por_unidad', models.FloatField(default=0)),
                ('peso_por_unidad', models.FloatField(default=0)),
                ('estado', models.BooleanField(default=False)),
                ('imagen', models.ImageField(blank=True, null=True, upload_to='proveedores')),
                ('link', models.CharField(blank=True, max_length=250)),
                ('fecha_actualizacion', models.DateTimeField(auto_now_add=True)),
                ('id_product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.product')),
                ('marca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.marcas')),
                ('proveedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.proveedores')),
                ('unidad_medida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.unidadmedida')),
            ],
            options={
                'verbose_name': 'ProveedorArticulos',
                'verbose_name_plural': 'ProveedorArticulos',
                'ordering': ['nombre_articulo'],
                'unique_together': {('proveedor', 'codigo_prod_prov', 'unidad_medida', 'nombre_articulo')},
            },
        ),
        migrations.CreateModel(
            name='ComprasEnc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_compra', models.DateField(blank=True, null=True)),
                ('observacion', models.TextField(blank=True, null=True)),
                ('sub_total', models.FloatField(default=0)),
                ('costoenvio', models.FloatField(default=0)),
                ('descuento', models.FloatField(default=0)),
                ('total', models.FloatField(default=0)),
                ('estado', models.IntegerField(default=0)),
                ('id_pago', models.IntegerField(blank=True, default=0, null=True)),
                ('proveedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.proveedores')),
            ],
            options={
                'verbose_name': 'Encabezado Compra',
                'verbose_name_plural': 'Encabezado Compras',
            },
        ),
        migrations.CreateModel(
            name='ComprasDet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.BigIntegerField(default=0)),
                ('precio_prv', models.FloatField(default=0)),
                ('sub_total', models.FloatField(default=0)),
                ('descuento', models.FloatField(default=0)),
                ('total', models.FloatField(default=0)),
                ('id_compra_enc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.comprasenc')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.proveedorarticulos')),
            ],
        ),
        migrations.CreateModel(
            name='CompraDolar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField()),
                ('monto', models.FloatField(default=0)),
                ('estado', models.BooleanField(default=False)),
                ('cuenta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.cuentas')),
            ],
            options={
                'verbose_name': 'CompraDolar',
                'verbose_name_plural': 'CompraDolares',
            },
        ),
    ]
