from django.urls import path, include
from . import views

urlpatterns = [ 
 
  path('', views.compras_home, name='compras'),
  path('solicitud/', views.compras_save, name='compras_save'),
  path('solicitud/detalle/<int:sol_id>', views.compras_usd_detalle, name='compras_usd_detalle'),
  path('solicitud/list/', views.compras_list, name='compras_list'),
  path('solicitud/close/<int:sol_id>', views.compras_close, name='compras_close'),
  path('solicitud/del/<int:sol_id>', views.compras_usd_delete, name='compras_usd_delete'),

  #Proveedores 
  path('proveedores/', views.proveedores_list, name='proveedores_list'),
  path('proveedores/add', views.proveedores_add, name='proveedores_add'),
  path('proveedores/update/<int:prov_id>', views.proveedores_update, name='proveedores_update'),
  path('proveedores/del/<int:prov_id>', views.proveedores_del, name='proveedores_del'),
  #Lista de precios proveedores
  path('proveedores/list/<int:prov_id>', views.proveedor_list_articulos, name='proveedor_list_articulos'),
  path('proveedores/art/<int:prov_id>/<int:prod_id>', views.proveedor_articulo, name='proveedor_articulo'),
  path('proveedores/vincular/', views.vincular_articulo, name='vincular_articulo'),
  path('proveedores/get_productos/<int:proveedor_id>/', views.get_productos, name='get_productos'),
  path('proveedores/check/', views.proveedor_check_articulos, name='proveedor_check_articulos'),
  path('proveedores/art/del/<int:prod_id>', views.prod_prov_del, name='proveedor_articulo_del'),
  

  #Ordenes de Compra
  path('oc/', views.generar_orden_compra, name='generar_orden_compra'),
  path('oc/procesar-datos/', views.procesar_datos, name='procesar_datos'),
  path('oc/list/', views.oc_list, name='oc_list'),
  path('oc/list/<int:id_oc>', views.oc_delete, name='oc_delete'),
  path('oc/<int:id_oc>', views.oc_detalle, name='oc_detalle'),
  path('oc/ver/<int:id_oc>', views.oc_detalle_ver, name='oc_detalle_ver'),
  path('oc/recibir/<int:id_oc>', views.oc_recibir, name='oc_recibir'),
  path('oc/anular/<int:id_oc>', views.oc_anula_recepcion, name='oc_anula_recepcion'),
  
  path('oc/anular_pago/<int:id_oc>', views.oc_anular_pago, name='oc_anular_pago'), 
  path('oc/pago/<int:id_oc>', views.oc_registrar_pago, name='oc_registrar_pago'), 
  


]