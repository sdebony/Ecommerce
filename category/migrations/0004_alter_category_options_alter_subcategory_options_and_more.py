# Generated by Django 4.2.4 on 2023-11-11 16:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0003_remove_subcategory_sub_category_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['category_name'], 'verbose_name': 'category', 'verbose_name_plural': 'categories'},
        ),
        migrations.AlterModelOptions(
            name='subcategory',
            options={'ordering': ['subcategory_name'], 'verbose_name': 'Sub Category', 'verbose_name_plural': 'Sub Categories'},
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='category.category', unique=True),
        ),
    ]