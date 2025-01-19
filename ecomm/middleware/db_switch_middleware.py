from django.conf import settings
from django.db import connections
from django.utils.deprecation import MiddlewareMixin

class DatabaseSwitchMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(':')[0]  # Obtén el hostname de la URL

        if host in ["127.0.0.1", "lifche.qualities.com.ar"]:
            # Configuración para 127.0.0.1
            connections.databases['default']['NAME'] = 'db.sqlite3'
            settings.DEF_CATEGORY = 'esferas'
            settings.DEF_SUBCATEGORY = 'esferas-9-mm'
            settings.DEF_CATEGORY_ADD_PROD = 'esferas'
            settings.DEF_SUBCATEGORY_ADD_PROD = 'esferas-9-mm'
            settings.STORE_MULTI_CANAL="NO"
            settings.STORE_DEF_CANAL="WEB"
            settings.STORE_TEMPLATE_MOBILE="3" # 1 Menu Mariano  /  3 MENU Test New
            settings.STORE_TEMPLATE="2"  #2 Menu original
            settings.ACTIVAR_ALERTAS = "NO"
            settings.DEF_CEL =  '54111558679809'
            settings.DEF_CC_MAIL = 'lifche.argentina@gmail.com'
            
        if host in ["localhost", "shop.qualities.com.ar"]:
            # Configuración para localhost
            connections.databases['default']['NAME'] = 'db.qualities.sqlite3'
            settings.DEF_CATEGORY = 'pelotas-de-tenis'
            settings.DEF_SUBCATEGORY = 'pelotas-de-tenis-odea'
            settings.DEF_CATEGORY_ADD_PROD = 'pelotas-de-tenis'
            settings.DEF_SUBCATEGORY_ADD_PROD = 'pelotas-de-tenis-a-granel'
            settings.DEF_CC_MAIL = 'qualitiesarg@gmail.com'
            settings.DEF_CEL = '54111565184759'
            settings.STORE_MULTI_CANAL="SI"
            settings.STORE_DEF_CANAL="WEB"
            settings.STORE_TEMPLATE_MOBILE="3" # 1 Menu Mariano  /  3 MENU Test New
            settings.STORE_TEMPLATE="2"  #2 Menu original
            settings.ACTIVAR_ALERTAS = "SI"
           

    