from django.urls import path, include
from . import views

urlpatterns = [ 
 
  path('cuentas', views.cuentas_list, name='conta_list_cuentas'),
  path('cuentas/<int:cta_id>', views.cuentas_detalle, name='conta_cuentas_detalle'),
  path('cuentas/', views.cuentas_new, name='conta_cuentas_new'),

]