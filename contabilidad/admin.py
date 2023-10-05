from django.contrib import admin

from .models import Transferencias,Movimientos,Operaciones,Cuentas,Monedas

# Register your models here.
admin.site.register(Transferencias)
admin.site.register(Movimientos)
admin.site.register(Operaciones)
admin.site.register(Cuentas)
admin.site.register(Monedas)
