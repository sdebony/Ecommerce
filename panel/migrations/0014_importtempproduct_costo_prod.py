# Generated by Django 4.2.4 on 2024-09-20 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel', '0013_importtempproduct_ubicacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='importtempproduct',
            name='costo_prod',
            field=models.FloatField(blank=True, default=0),
        ),
    ]