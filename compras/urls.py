from django.urls import path, include
from . import views

urlpatterns = [ 
 
  path('', views.compras_home, name='compras'),
  path('solicitud/', views.compras_save, name='compras_save'),
  path('solicitud/detalle/<int:sol_id>', views.compras_usd_detalle, name='compras_usd_detalle'),
  path('solicitud/list/', views.compras_list, name='compras_list'),
  path('solicitud/close/<int:sol_id>', views.compras_close, name='compras_close'),
  path('solicitud/del/<int:sol_id>', views.compras_usd_delete, name='compras_usd_delete'),

  
 
  
]