from django.contrib import admin
from .models import Category

# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('category_name',)} #Replica lo de category_name es campo slug
    list_display = ('category_name','slug')
    
admin.site.register(Category,CategoryAdmin)
