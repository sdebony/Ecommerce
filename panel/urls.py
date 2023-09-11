from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel_home, name='panel'),
    #PRODUCTOS
    path('catalogo/', views.panel_product_list, name='panel_catalogo'),
    path('producto/<int:product_id>', views.panel_product_detalle, name='panel_producto_detalle'),
    path('producto/', views.panel_product_crud, name='panel_producto_crud'),
    path('producto/img', views.panel_producto_img, name='panel_producto_img'),
    path('producto/variant/', views.panel_productos_variantes, name='panel_producto_variante'),
    path('producto/variant_del/', views.panel_productos_variantes_del, name='panel_producto_variante_del'),
    #PEDIDOS
    path('pedidos/', views.panel_pedidos_list, name='panel_pedidos'),
    
]
