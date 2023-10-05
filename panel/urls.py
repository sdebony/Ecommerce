from django.urls import path
from . import views


urlpatterns = [
    path('', views.panel_home, name='panel'),
    path('dashboard/ventas', views.dashboard_ventas, name='dashboard_ventas'),
    #PRODUCTOS
    path('catalogo/', views.panel_product_list, name='panel_catalogo'),
    path('producto/<int:product_id>', views.panel_product_detalle, name='panel_producto_detalle'),
    path('producto/', views.panel_product_crud, name='panel_producto_crud'),
    path('producto/img', views.panel_producto_img, name='panel_producto_img'),
    path('producto/variant/', views.panel_productos_variantes, name='panel_producto_variante'),
    path('producto/variant_del/', views.panel_productos_variantes_del, name='panel_producto_variante_del'),
    path('producto/import/productos/', views.import_productos_xls, name='panel_producto_import'), 
    path('producto/import/', views.panel_importar_productos, name='panel_importar_productos'),
    path('producto/save/', views.guardar_tmp_productos, name='panel_guardar_tmp_productos'),
    path('producto/habilitar/<int:product_id>/<int:estado>', views.panel_producto_habilitar, name='panel_producto_habilitar'),
    path('producto/import/del/<int:product_id>', views.panel_importar_productos_del, name='panel_importar_productos_del'),
    
    #CATEGORIAS
    path('categoria/', views.panel_categoria_list, name='panel_categoria'),
    path('categoria/<int:categoria_id>', views.panel_categoria_detalle, name='panel_categoria_detalle'),
    path('categoria/new', views.panel_categoria_detalle, name='panel_categoria_new'),
    path('categoria/del/<int:id_categoria>', views.panel_categoria_del, name='panel_categoria_del'),
    path('categoria/save/', views.panel_categoria_detalle, name='panel_categoria_save'),

    #PEDIDOS
    #path('pedidos/', views.panel_pedidos_list, name='panel_pedidos'),
    path('pedidos/<str:status>', views.panel_pedidos_list, name='panel_pedidos'),
    path('pedidos/detalle/<str:order_number>', views.panel_pedidos_detalle, name='panel_pedidos_detalle'),
    path('pedidos/pagos/<str:order_number>', views.panel_registrar_pago,name='registrar_pago'),
    path('pedidos/pagos/confir/<str:order_number>', views.panel_confirmar_pago,name='confirmar_pago'),
    path('pedidos/import/pedidos/', views.import_pedidos_xls, name='panel_pedidos_import'),
    path('pedidos/import/pedidos/one/<str:codigo>', views.guardar_tmp_pedidos, name='panel_guardar_tmp_pedidos'),
    path('pedidos/import/pedidos/all/', views.guardar_tmp_pedidos_all, name='panel_guardar_tmp_pedidos_all'), 
    path('pedidos/entregas/<str:order_number>', views.panel_registrar_entrega, name='panel_registrar_entrega'), 
    path('pedidos/entregas/', views.panel_confirmar_entrega, name='panel_confirmar_entrega'), 
    path('pedidos/eliminar/pago/<str:order_number>', views.panel_pedidos_eliminar_pago, name='panel_pedidos_eliminar_pago'), 
    path('pedidos/eliminar/<str:order_number>', views.panel_pedidos_eliminar, name='panel_pedidos_eliminar'), 
    path('pedidos/eliminar/entrega/<str:order_number>', views.panel_pedidos_eliminar_entrega, name='panel_pedidos_eliminar_entrega'), 
     
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

    
    
    
    
]
