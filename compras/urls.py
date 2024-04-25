from django.urls import path, include
from . import views

urlpatterns = [ 
 
  path('', views.compras_home, name='compras'),
  path('search/<str:keyword>', views.search_proveedor_lookup, name='search_proveedor_lookup'),
  
]