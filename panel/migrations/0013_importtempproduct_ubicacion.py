# Generated by Django 4.2.4 on 2024-09-16 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panel', '0012_remove_importtemporders_dir_correo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='importtempproduct',
            name='ubicacion',
            field=models.FloatField(blank=True, default=0),
        ),
    ]