from django.urls import path, include
from . import views

urlpatterns = [ 
 
  path('config/', views.meli_list, name='meli_list'),
  path('config/refresh/', views.meli_solicitar_refresh_token, name='meli_solicitar_token'),
  path('', views.meli_save_token, name='meli_save_token'),  # Redireciona para salvar o token obtido na url de autenticação do ML  localhost:8000/meli 
  path('config/get_token/', views.meli_get_first_token, name='meli_get_first_token'),
  path('meli/vendor/', views.meli_productos_vendor_detail, name='meli_productos_vendor_detail'),

  
  

  

]