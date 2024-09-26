"""
URL configuration for ecomm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from . import views



urlpatterns = [
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    #path('admin/', admin.site.urls),
    path('securelogin/', admin.site.urls),
    path('', views.home, name='home'),
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('accounts/', include('accounts.urls')),
    # ORDERS
    path('orders/', include('orders.urls')),
    # PANEL DE ADMINISTRACION
    path('panel/', include('panel.urls')),
    #APIS
    path('api/', include(('api.urls', 'api'), namespace='api')),
    #CONTABILIDAD - REGISTRACION DE MOVIMIENTOS CONTABLES
    path('cont/', include('contabilidad.urls')),
    #MELI
    path('meli/', include('meli.urls')),
    #COMPRAS
    path('compras/', include('compras.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



