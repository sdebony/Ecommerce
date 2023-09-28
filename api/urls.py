from django.urls import path, include
from .views import DireccionesList, Direccion

urlpatterns = [ 
    path('v1/direccion/<int:dir_id>',Direccion.as_view(),name='api_direccion'),
    path('v1/direccion/',DireccionesList.as_view(),name='api_direccion'),


]