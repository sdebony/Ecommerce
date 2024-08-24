from django.contrib import admin
from .models import  ImportTempOrders,ImportTempOrdersDetail,ImportTempProduct

# Register your models here.

class TempProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'description', 'variation_category', 'variation_value', 'price','images','stock','is_available','category','created_date','modified_date','usuario')
    prepopulated_fields = {'slug': ('product_name',)}
    list_editable = ('is_available',)
    list_filter = ('product_name', 'variation_category', 'variation_value')
    

class TempOrderAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'first_name', 'last_name', 'email', 'created_at','updated_at','order_total','dir_telefono','dir_calle','dir_nro','dir_localidad','dir_provincia','dir_cp','dir_obs','dir_tipocorreo')
    list_filter = ('codigo', 'first_name', 'last_name')


class TempOrderDetailAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'product', 'quantity', 'subtotal')
    list_filter = ('codigo', 'product', 'quantity', 'subtotal')


admin.site.register(ImportTempOrders)
admin.site.register(ImportTempOrdersDetail)
admin.site.register(ImportTempProduct)
