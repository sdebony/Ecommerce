# Generated by Django 4.2.4 on 2024-01-14 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0007_alter_subcategory_sub_category_slug_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='orden',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='orden',
            field=models.IntegerField(default=0),
        ),
    ]