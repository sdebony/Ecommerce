from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


from .serializers import DireccionesSerializer,CuentasSerializer, SubcategorySerializer
from accounts.models import AccountDirecciones,Account
from contabilidad.models import Cuentas
from category.models import SubCategory
from panel.models import ImportDolar


from django.db.models import Q

from django.conf import settings

from datetime import datetime,timezone,timedelta


# views.py
from django.http import JsonResponse
import requests
import json

#http://localhost:8000/api/v1/enviar_whatsapp/
def enviar_whatsapp(request,nro_orden,telefono):
    url = settings.WHATSAPP_URL_ENVIO    # Reemplaza esto con la URL de la API a la que deseas enviar los datos
   
   #VERSION pywhatkit Browser
   # import pywhatkit
   # import datetime, time
   # print("enviar_whatsapp activado:" + str(telefono))
   # hora = datetime.datetime.now()
   # hora_to_send = hora.hour
   # minuto_to_send = hora.minute

   # mensaje = "Gracias por su compra. Tu pedido es el Nro: " + str(nro_orden)
   # pywhatkit.sendwhatmsg_instantly("+"+ str(telefono),mensaje) #"+54111565184759"
   # #pywhatkit.sendwhatmsg("+"+ str(telefono), mensaje,hora_to_send,minuto_to_send,False,3)
   # print("Fin envio whathapp. send to: +" + str(telefono) + " Hora: " + str(hora_to_send) + ":" + str(minuto_to_send))
   # https://www.youtube.com/watch?v=u069FuQeSxE
    if nro_orden:
        if nro_orden:
            # JSON que deseas enviar a la API
            json_data = {
                "messaging_product": "whatsapp", 
                "to": telefono, #"+54111565184759", 
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
                    print("Mensaje enviado correctamente")
                    return JsonResponse({'mensaje': 'Datos enviados correctamente'}, status=200)
                else:
                    print("Error al enviar el mensaje. Error Status:", str(response.status_code))
                    return JsonResponse({'error': 'Hubo un problema al enviar los datos'}, status=response.status_code)
            except Exception as e:
                print("Error Exception al enviar el mensaje")
                return JsonResponse({'error': str(e)}, status=500)
        else:
            print("WHATSAPP: ERROR: No se encontro nro de telefono")
    else:
        print("WHATSAPP: ERROR: No se encontro nro de orden")

#http://localhost:8000/api/v1/dolar/
def GuardarDolar(request):
    
    response = requests.get("https://dolarapi.com/v1/dolares/blue")
    data = response.json()

    print(data)

    
    if response.status_code == 200:

        codigo = data['casa']
        moneda = data['moneda']
        nombre = data['nombre']
        compra = data['compra']
        venta = data['venta']
        promedio = (compra + venta ) / 2
        fecha = data['fechaActualizacion']
        fecha_str = str(fecha)
        d=datetime.fromisoformat(fecha_str[:-1]).astimezone(timezone.utc)
        fecha_str = d.strftime('%Y-%m-%d %H:%M:%S') 
        fecha_str = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S") - timedelta(hours=4)
        
        dia = datetime.today()
        dia_str = dia.strftime('%Y-%m-%d')

        dolar = ImportDolar.objects.filter(created_at=dia_str).first()
        if dolar:
            doar_cot = ImportDolar(
                id = dolar.id,
                created_at  = dia_str, #Fecha de día
                codigo      = codigo, 
                moneda      = moneda,
                nombre      =  nombre,
                compra      = compra,
                venta       = venta,
                promedio    = promedio,
                fechaActualizacion = fecha_str #Fecha y Hora de ultima actualizacion   
            )   
            doar_cot.save()
        else:
            doar_cot = ImportDolar(
                created_at  = dia_str, #Fecha de día
                codigo      = codigo, 
                moneda      = moneda,
                nombre      =  nombre,
                compra      = compra,
                venta       = venta,
                promedio    = promedio,
                fechaActualizacion = fecha_str #Fecha y Hora de ultima actualizacion   
            )   
            doar_cot.save()
            
            
        return JsonResponse({'mensaje': 'Dolar actualizado correctamente'}, status=200)
       
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

     
     