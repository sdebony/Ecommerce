from django.contrib import admin
from .models import Category,SubCategory

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug')


class SubCategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'sub_category_slug': ('subcategory_name',)}
    list_display = ('category','subcategory_name', 'sub_category_slug')


admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
