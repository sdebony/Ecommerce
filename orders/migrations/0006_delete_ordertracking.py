# Generated by Django 4.2.4 on 2024-03-01 08:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_fecha_tracking_order_nro_tracking'),
    ]

    operations = [
        migrations.DeleteModel(
            name='OrderTracking',
        ),
    ]