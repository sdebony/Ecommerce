from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


from .serializers import DireccionesSerializer,CuentasSerializer, SubcategorySerializer
from accounts.models import AccountDirecciones,Account
from contabilidad.models import Cuentas
from category.models import SubCategory

from django.db.models import Q

from django.conf import settings



# views.py
from django.http import JsonResponse
import requests
import json


#http://localhost:8000/api/v1/enviar_whatsapp/

def enviar_whatsapp(request,nro_orden,telefono):
    url = settings.WHATSAPP_URL_ENVIO    # Reemplaza esto con la URL de la API a la que deseas enviar los datos

#print("entra aqui")
    if nro_orden:
        if nro_orden:
            # JSON que deseas enviar a la API
            json_data = {
                "messaging_product": "whatsapp", 
                "to": telefono, #"54111565184759", 
                "type": "template", 
                "template": { 
                    "name": "gracias_por_su_compra",
                    "language": { 
                        "code": "es_AR" 
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "text": nro_orden
                                }
                            ]
                        }
                    ]
                }
            }

            headers = {
                'Authorization': settings.WHATSAPP_TOKEN ,  # Reemplaza 'tu_token_de_autorización' con tu token real
                'Content-Type': 'application/json'
            }

            try:
                # Realiza la solicitud POST a la API con los datos JSON y los encabezados
                response = requests.post(url, json=json_data, headers=headers)
                
                # Verifica el código de estado de la respuesta
                if response.status_code == 200:
                    return JsonResponse({'mensaje': 'Datos enviados correctamente'}, status=200)
                else:
                    return JsonResponse({'error': 'Hubo un problema al enviar los datos'}, status=response.status_code)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            print("WHATSAPP: ERROR: No se encontro nro de telefono")
    else:
        print("WHATSAPP: ERROR: No se encontro nro de orden")




class Direccion(APIView):
          
    def get(self,request,dir_id):
        print("Direccion API ",dir_id)
        if dir_id==99:
            user_id = Account.objects.filter(email=settings.EMAIL_HOST_USER).first()
            print("Retira por capital. direccion 99 lifche usuario ",user_id)
            if user_id:
                direccion = get_object_or_404(AccountDirecciones,user=user_id)
        else:
            direccion = get_object_or_404(AccountDirecciones,dir_id=dir_id)
        data = DireccionesSerializer(direccion).data
        print(data)
        return Response(data)


class DireccionesList(APIView):
          
    def get(self,request):
        print("Lista de Direcciones")
        direccion = get_object_or_404(AccountDirecciones)
        data = DireccionesSerializer(direccion,many=True).data
        return Response(data)

class CuentasList(APIView):
          
    def get(self,request,cuenta):
        print("Cuentas API List")
        cuentas = get_object_or_404(Cuentas,Q(id=cuenta))
        data = CuentasSerializer(cuentas).data
        return Response(data)

class CuentasApi(APIView):
          
    def get(self,request):
        print("Cuentas API ")
        cuentas = Cuentas.objects.all()
        data = CuentasSerializer(cuentas,many=True).data
        return Response(data)

class SubcategoryList(APIView):
          
    def get(self,request,category):
        print("SubCategory API List")
        #subcategory = get_object_or_404(SubCategory,Q(category=category))
        subcategory = SubCategory.objects.filter(Q(category=category))
        data = SubcategorySerializer(subcategory,many=True).data
        return Response(data)

class SubcategoryApi(APIView):
          
    def get(self,request):
        print("SubCategory API ")
        subcategory = SubCategory.objects.all()
        data = SubcategorySerializer(subcategory,many=True).data
        return Response(data)


     
     