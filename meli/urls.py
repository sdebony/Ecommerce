from django.urls import path, include
from . import views

urlpatterns = [ 
 
  path('config/', views.meli_list, name='meli_list'),
  path('config/refresh/', views.meli_solicitar_refresh_token, name='meli_solicitar_token'),
  #path('meli/', views.meli_save_token, name='meli_save_token'),  # Redireciona para salvar o token obtido na url de autenticação do ML  localhost:8000/meli 
  path('', views.meli_save_token, name='meli_save_token'), 
  path('config/get_token/', views.meli_get_first_token, name='meli_get_first_token'),
  path('meli/vendor/', views.meli_productos_vendor_detail, name='meli_productos_vendor_detail'),
 
 
  path('search/', views.meli_search, name='meli_search'),
  path('search/categoria/<str:categoria_id>', views.meli_search_categoria, name='meli_search_categoria'),
  path('publicacones/', views.meli_publicaciones, name='meli_publicaciones'),
  path('ventas/', views.meli_ventas, name='meli_ventas'),
  path('ventas/detalle/<str:id_pedido_meli>', views.meli_ventas_detalle, name='meli_ventas_detalle'),
  path('ventas/detalle/guardar/', views.importar_pedido_meli, name='importar_pedido_meli'),
  path('analisis/<str:idpublicacion>', views.meli_analisis_publicaciones, name='meli_analisis_publicaciones'),
 
  
  

  

]