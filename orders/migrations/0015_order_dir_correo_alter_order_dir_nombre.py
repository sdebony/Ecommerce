# Generated by Django 4.2.4 on 2024-10-12 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_alter_order_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='dir_correo',
            field=models.BigIntegerField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='order',
            name='dir_nombre',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]