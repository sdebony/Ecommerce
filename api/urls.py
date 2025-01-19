from django.urls import path, include
from .views import DireccionesList, Direccion,DireccionesbyTipo,CuentasList,CuentasApi,SubcategoryList,CategoryList,ProductList, SubcategoryApi,enviar_whatsapp,GuardarDolar



urlpatterns = [ 
    path('v1/direccion/<int:dir_id>',Direccion.as_view(),name='api_direccion'),
    path('v1/direccion/',DireccionesList.as_view(),name='api_direccion'),

    #Busca la direccion seguen la seleccion del checkout
    path('v1/direccionbytipo/<str:correo_tipo>',DireccionesbyTipo.as_view(),name='api_buscardireccion_seleccion'),
    path('v1/direccionbytipo/',DireccionesbyTipo.as_view(),name='api_buscardireccion_seleccion'),

    path('v1/cuentas/',CuentasApi.as_view(),name='cuentas_list'),
    path('v1/cuentas/<int:cuenta>',CuentasList.as_view(),name='cuentas_list'),
    path('v1/category/',CategoryList.as_view(),name='category_list'),
    path('v1/products/<int:subcategory>',ProductList.as_view(),name='product_list'),
    
    path('v1/subcategory/<int:category>',SubcategoryList.as_view(),name='subcategory_list'),
    path('v1/subcategory/',SubcategoryApi.as_view(),name='subcategory_list'),
    path('v1/enviar_whatsapp/', enviar_whatsapp, name='enviar_whatsapp'),
    path('v1/dolar/', GuardarDolar, name='dolar'), #GuardarDolar
    
]