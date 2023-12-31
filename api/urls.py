from django.urls import path, include
from .views import DireccionesList, Direccion,CuentasList,CuentasApi



urlpatterns = [ 
    path('v1/direccion/<int:dir_id>',Direccion.as_view(),name='api_direccion'),
    path('v1/direccion/',DireccionesList.as_view(),name='api_direccion'),
    path('v1/cuentas/',CuentasApi.as_view(),name='cuentas_list'),
    path('v1/cuentas/<int:cuenta>',CuentasList.as_view(),name='cuentas_list'),


]

