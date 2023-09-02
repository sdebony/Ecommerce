from django.contrib import admin
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name','price','stock','category','modified_date','is_available','images')
    prepopulated_fields = {'slug' : ('product_name',)} #Replica lo de product_name es campo slug
    
    
admin.site.register(Product,ProductAdmin)