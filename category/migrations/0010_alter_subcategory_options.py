# Generated by Django 4.2.4 on 2024-03-26 21:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0009_alter_category_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subcategory',
            options={'ordering': ['orden'], 'verbose_name': 'Sub Category', 'verbose_name_plural': 'Sub Categories'},
        ),
    ]