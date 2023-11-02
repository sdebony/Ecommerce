from django.urls import path
from . import views


urlpatterns = [
    path('', views.panel_home, name='panel'),
    path('dashboard/ventas', views.dashboard_ventas, name='dashboard_ventas'),
    path('dashboard/cuentas', views.dashboard_cuentas, name='dashboard_cuentas'),
    #PRODUCTOS
    path('productos/list', views.panel_product_list_category, name="producto_list_category"),
    path('catalogo/', views.panel_product_list, name='panel_catalogo'),
    path('producto/<int:product_id>', views.panel_product_detalle, name='panel_producto_detalle'),
    path('producto/', views.panel_product_crud, name='panel_producto_crud'),
    path('producto/img', views.panel_producto_img, name='panel_producto_img'),
    path('producto/variant/', views.panel_productos_variantes, name='panel_producto_variante'),
    path('producto/variant_del/', views.panel_productos_variantes_del, name='panel_producto_variante_del'),
    path('producto/del/<int:product_id>', views.panel_productos_del, name='panel_productos_del'),

    path('producto/import/stock/', views.import_stock, name='panel_import_stock'), 
    path('producto/import/precios/', views.import_precios, name='panel_import_precios'), 
    path('producto/import/productos/', views.import_productos_xls, name='panel_producto_import'),
     
    path('producto/import/', views.panel_importar_productos, name='panel_importar_productos'),
    path('producto/save/', views.guardar_tmp_productos, name='panel_guardar_tmp_productos'),
    path('producto/habilitar/<int:product_id>/<int:estado>', views.panel_producto_habilitar, name='panel_producto_habilitar'),
    path('producto/import/del/<int:product_id>', views.panel_importar_productos_del, name='panel_importar_productos_del'),
    path('producto/search/<str:keyword>/<str:order_number>', views.search_lookup, name='search_lookup'),
    
    #CATEGORIAS
    path('categoria/', views.panel_categoria_list, name='panel_categoria'),
    path('categoria/<int:categoria_id>', views.panel_categoria_detalle, name='panel_categoria_detalle'),
    path('categoria/new', views.panel_categoria_detalle, name='panel_categoria_new'),
    path('categoria/del/<int:id_categoria>', views.panel_categoria_del, name='panel_categoria_del'),
    path('categoria/save/', views.panel_categoria_detalle, name='panel_categoria_save'),
    path('categoria/sub/<int:id_categoria>', views.panel_subcategoria_save, name='panel_subcategoria_save'),
    path('categoria/sub/del/<int:id_subcategoria>', views.panel_subcategoria_del, name='panel_subcategoria_del'),

    #PEDIDOS
    #path('pedidos/', views.panel_pedidos_list, name='panel_pedidos'),
    path('pedidos/<str:status>', views.panel_pedidos_list, name='panel_pedidos'),
    path('pedidos/detalle/<str:order_number>', views.panel_pedidos_detalle, name='panel_pedidos_detalle'),
    path('pedidos/detalle/edit/<str:order_number>', views.panel_pedidos_detalle_edit, name='panel_pedidos_detalle_edit'),
    path('pedidos/pagos/<str:order_number>', views.panel_registrar_pago,name='registrar_pago'),
    path('pedidos/pagos/confir/<str:order_number>', views.panel_confirmar_pago,name='confirmar_pago'),
    path('pedidos/import/pedidos/', views.import_pedidos_xls, name='panel_pedidos_import'),
    path('pedidos/import/pedidos/one/<str:codigo>', views.guardar_tmp_pedidos, name='panel_guardar_tmp_pedidos'),
    path('pedidos/import/pedidos/all/', views.guardar_tmp_pedidos_all, name='panel_guardar_tmp_pedidos_all'), 
    path('pedidos/entregas/<str:order_number>', views.panel_registrar_entrega, name='panel_registrar_entrega'), 
    path('pedidos/entregas/', views.panel_confirmar_entrega, name='panel_confirmar_entrega'), 
    path('pedidos/eliminar/pago/<str:order_number>', views.panel_pedidos_eliminar_pago, name='panel_pedidos_eliminar_pago'), 
    path('pedidos/eliminar/<str:order_number>', views.panel_pedidos_eliminar, name='panel_pedidos_eliminar'), 
    path('pedidos/eliminar/conf/<str:order_number>', views.panel_pedidos_confirmacion_eliminar, name='panel_pedidos_confirmacion_eliminar'),
    path('pedidos/save/', views.panel_pedidos_save_enc, name='panel_pedidos_save_enc'), 
     path('pedidos/mail/<str:order_number>', views.panel_pedidos_enviar_factura, name='panel_pedidos_enviar_factura'), 
    
    path('pedidos/eliminar/entrega/<str:order_number>', views.panel_pedidos_eliminar_entrega, name='panel_pedidos_eliminar_entrega'), 
    path('pedidos/detalle/modif/<str:order_number>/<str:item>/<str:quantity>', views.panel_pedidos_modificar, name='panel_pedidos_modificar'), 
    path('pedidos/detalle/modif/line/<int:item>', views.panel_pedidos_obtener_linea, name='panel_pedidos_modificar_linea'), 
    path('pedidos/detalle/save/line', views.panel_pedidos_save_detalle, name='panel_pedidos_save_detalle'), 
    path('pedidos/detalle/del/line/<str:order_number>/<int:id_linea>', views.panel_pedidos_del_detalle, name='panel_pedidos_del_detalle'), 
     
     

     

     
    #USUARIOS
    path('usuarios/', views.panel_usuario_list, name='panel_usuarios'),
    #    *****Listado de usuario
    path('usuarios/permisos/<int:user_id>', views.panel_usuario_permisos, name='panel_usuarios_permisos'), 
    #   ******Detalle del usuario
    path('usuarios/permisos/reasignar/<int:user_id>', views.panel_usuario_permisos_reasignar, name='panel_usuarios_reasignar'), 
    #   ****** Actualizacion
    path('usuarios/permisos/reasignar/<int:user_id>/<int:id_pk>/<int:codigo>/<int:tipo>/<int:valor>', views.panel_usuario_permisos_actualizar, name='panel_usuario_permisos_actualizar'), 
    path('usuarios/profile', views.panel_edit_profile, name='panel_usuarios_profile'),
    #CLIENTES
    path('clientes/', views.panel_cliente_list, name='panel_clientes'),
    path('clientes/detalle/<int:id_cliente>', views.panel_cliente_detalle, name='panel_clientes_detalle'),
    #MOVIMIENTOS
    path('mov/', views.panel_movimientos_list, name='panel_movimientos'),
    path('mov/export_xls/<int:modelo>',views.export_xls, name="mov_export_xls"),
    path('mov/transferencia/<int:idtrans>',views.panel_movimientos_transf, name="mov_transferencia"),
    path('mov/tranf/', views.panel_transferencias_list, name='panel_transferencias'),
    path('mov/tranf/del/<int:idtrans>', views.panel_transferencias_eliminar, name='panel_transferencias_eliminar'),
    path('mov/registros/<int:idmov>',views.registrar_movimiento, name="mov_registros"),
    path('mov/mov/del/<int:idmov>', views.panel_movimiento_eliminar, name='panel_movimiento_eliminar'),
    path('mov/cierre/calcular', views.panel_cierre_registrar, name='panel_cierre_registrar'),
    
    

    
    
    
    
]
