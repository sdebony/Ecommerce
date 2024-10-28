
from django.shortcuts import render, get_object_or_404,redirect
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import AccountPermition
from meli.models import meli_params
from django.contrib import messages
from orders.models import Order
from accounts.models import UserProfile

from datetime import datetime

import requests
from django.http import JsonResponse
import json
# Create your views here.

from django.conf import settings

def meli_get_authorization_code(client_id):


    print("meli_get_authorization_code. Cliente ID:", client_id)
    authorization_code = meli_params.objects.filter(client_id=client_id).first()
    
    if not authorization_code:
        access_token = ""   
        print("ERROR: meli_get_authorization_code")
        
    
    else:
        access_token = authorization_code.access_token
        print("Tomo el access token de la base:",access_token)
    
    return  access_token

def meli_list(request):

    print("***********  meli_list ************")
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    
      
        context = {
            'permisousuario':permisousuario,
           
        }
       
        return render(request,'meli/meli_config.html',context) 

    return render(request,'panel/login.html',)

#Paso 1
def meli_get_first_token(request):

    print("meli_get_first_token")

    try:
        if request.user.is_authenticated:
            print("Usuario Autenticado")
            #accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            accesousuario =  AccountPermition.objects.get(user=request.user,codigo__codigo ='CONFIG ML')

            if accesousuario:
                if accesousuario.modo_ver==True:
                   print("Con Acceso a ML ")
                   #return redirect('panel')
                      
            else:
                print("Sin Acceso ML")
                orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
                orders_count = orders.count()

                userprofile = UserProfile.objects.get(user_id=request.user.id)
        
                context = {
                    'orders_count': orders_count,
                    'userprofile': userprofile,
                }
                return redirect("dashboard")     
        else:
            print("Usuario No Autenticado")
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
        
       
        orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
        orders_count = orders.count()

        userprofile = UserProfile.objects.get(user_id=request.user.id)

        context = {
            'orders_count': orders_count,
            'userprofile': userprofile,
        }
        return redirect("dashboard")  

    
    if accesousuario.codigo.codigo =='CONFIG ML':
       url = "https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id=" + settings.CLIENTE_ID  +  "&redirect_uri=" + settings.REDIRECT_URI 
       return redirect(url)
    else:
     
        return redirect('panel')
#Paso 2     
def meli_save_token(request):

    print("save token")

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':


            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            context = {
                'permisousuario':permisousuario,
            }    

            code = request.GET.get('code')
            if code:
                cliente_id = settings.CLIENTE_ID
                token = meli_params.objects.get(client_id=cliente_id)
                if token:     
                    token = meli_params(
                        id = token.id,
                        client_id = cliente_id,
                        code = code,
                        refresh_token = token.refresh_token,
                        access_token= token.access_token,
                        token_type= token.token_type,
                        userid= token.userid,
                        last_update=datetime.today(),
                    
                    )        
                    token.save()
                    meli_solicitar_refresh_token(request)

                    messages.success(request,"Token guardado con exito.")
                else:
                    messages.warning(request,"No se ha podido obtener el codigo de autorizacion.")

          
        
            return redirect('panel')

    else:
        return render(request,'panel/login.html',)
#Paso 3
def meli_solicitar_refresh_token(request):

    print("meli_solicitar_token")

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        context = {
            'permisousuario':permisousuario,
        }    


        cliente_id = settings.CLIENTE_ID
        refresh_token = meli_params.objects.get(client_id=cliente_id)
        if refresh_token:
            code = refresh_token.code 


        url = "https://api.mercadolibre.com/oauth/token"

        payload = 'grant_type=authorization_code&client_id='+ str(cliente_id)+ '&code='+ str(code) +'&redirect_uri='+ str(settings.REDIRECT_URI)+'&client_secret=' + settings.CLIENT_SECRET
        headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded'
        }

        
        response = requests.request("POST", url, headers=headers, data=payload)

        # Verifica el código de estado de la respuesta
        if response.status_code == 200:
            resp = json.loads(response.text)
            
            access_token = resp['access_token']
            token_type = resp["token_type"]
            user_id = resp["user_id"]
            refreshtoken=resp["refresh_token"]

            print("Nuevos Datos *******")
            print("")
            print("Access Token: ", access_token)
            print("Token Type: ", token_type)
            print("User ID: ", user_id)
            print("Refresh Token: ", refreshtoken)
            print("")
            print("*************************")
            refresh_token = meli_params.objects.get(client_id=cliente_id)
            if refresh_token:     
                refresh_token = meli_params(
                id = refresh_token.id,
                client_id = cliente_id,
                code = refresh_token.code,
                refresh_token = refreshtoken,
                access_token= 'Bearer ' + access_token,
                token_type= token_type,
                userid= user_id,
                last_update=datetime.today(),
                
                )        
                refresh_token.save()
                try:
                    print("DATOS:",access_token,token_type,refresh_token,user_id) 
                    messages.success(request,"REFRESH TOKEN  guardado con exito.")
                
                except ObjectDoesNotExist:
                    print("Error: meli_solicitar_refresh_token")
                    messages.error(request,"ERROR: REFRESH TOKEN.")
            
        else:
            messages.error(request,"ERROR: REFRESH TOKEN. Error Code Status:" + str(response.status_code))
            
        #return redirect('panel') 
        return render (request,"panel/base.html",context)

    else:
        return render(request,'panel/login.html',)

def meli_productos_vendor_detail(request):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        articulos = []
      
        if request.method =="POST":
            nick_name = request.POST.get("nick_name")
            if nick_name.isnumeric():
                url = "https://api.mercadolibre.com/sites/MLA/search?seller_id=" + str(nick_name)
            else:
                url = "https://api.mercadolibre.com/sites/MLA/search?nickname=" + str(nick_name)



            access_token = meli_get_authorization_code(settings.CLIENTE_ID)
            payload = {}
            headers = {
                'Authorization': access_token #'APP_USR-5374552499309003-040715-531af5500eba214cfed3597ccc74e677-4388206'
            }
            
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code==200 : 

                response_json = json.loads(response.text) #Diccionario
                
                articulos = response_json
            else:
                messages.error(request,"Error de conexion  en Mercado Libre.")
                print("ERROR DE CONEXION")

        
        context = {
            'permisousuario':permisousuario,
            'articulos':articulos,
        }

        return render(request,'meli/meli_vendor_detail.html',context) 

    return render(request,'panel/login.html',)

def meli_search_categoria(request, categoria_id):
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        arts_category = []
        print("--> categoria:",categoria_id)
      
        if request.method =="POST":
            str_search = request.POST.get("str_search")
            str_search = str_search.replace(" ","%20")
            url = "https://api.mercadolibre.com/sites/MLA/search?q=" + str(str_search) + "&category=" + str(categoria_id)
        else:
            url = "https://api.mercadolibre.com/categories/" + str(categoria_id) 
        

        print("url:", url)
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        payload = {}
        headers = {
            'Authorization': access_token #'APP_USR-5374552499309003-040715-531af5500eba214cfed3597ccc74e677-4388206'
        }
        
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code==200 : 

            response_json = json.loads(response.text) #Diccionario
            
            arts_category = response_json

           
        else:
            messages.error(request,"Error de conexion  en Mercado Libre.")
            print("ERROR DE CONEXION")

        
        context = {
            'permisousuario':permisousuario,
            'arts_category':arts_category,
        }

        return render(request,'meli/meli_search_category.html',context) 

    return render(request,'panel/login.html',)

def meli_search(request):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        articulos = []
        str_search=""
        if request.method =="POST":
            str_search = request.POST.get("str_search")
            str_search = str_search.replace(" ","%20")

            url = "https://api.mercadolibre.com/sites/MLA/search?q=" + str(str_search)
           
            #offset=0
            #params = {"q": str_search, "offset": offset}
            access_token = meli_get_authorization_code(settings.CLIENTE_ID)
            payload = {}
            headers = {
                'Authorization': access_token #'APP_USR-5374552499309003-040715-531af5500eba214cfed3597ccc74e677-4388206'
            }
            #response = requests.request("GET", url, headers=headers, params=params)
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code==200 : 

                response_json = json.loads(response.text) #Diccionario
                
                articulos = response_json
                print("***********************")
                #print(articulos)
                print("**********************")
            else:
                messages.error(request,"Error de conexion  en Mercado Libre.")
                print("ERROR DE CONEXION")

        
        context = {
            'permisousuario':permisousuario,
            'articulos':articulos,
            'str_search':str_search
        }

        return render(request,'meli/meli_search.html',context) 

    return render(request,'panel/login.html',)

def meli_publicaciones(request):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':

        print("Mis publicaciones")
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
        publicaciones=''
        publicaciones = meli_get_all_publicaciones(request)
        print(publicaciones)

        # Busca los detalles de los artículos
        url = "https://api.mercadolibre.com/items?ids=" + str(publicaciones)
        
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        
        payload = {}
        headers = {
            'Authorization': access_token #'APP_USR-710125811010660-102410-fc5f755c5fbdf1b370dd274c57b7e838-1998248263'
        }

        articulos=[]
        detail_response = requests.request("GET", url, headers=headers, data=payload)
        
        if detail_response.status_code == 200:
            articulos = detail_response.json()  # Detalles de los artículos
            

        else:
            print(f"Error al obtener los detalles de los productos: {detail_response.status_code}")
            print(f"Contenido de la respuesta: {detail_response.text}")
            messages.error(request, f"Error en la conexión con Mercado Libre - Detalle Productos ({detail_response.status_code})")


       

        
        context = {
            'permisousuario':permisousuario,
            'articulos':articulos
        }

        return render(request,'meli/meli_publicaciones.html',context) 

    return render(request,'panel/login.html',)

def meli_get_all_publicaciones(request):
    # Obtiene la lista de publicaciones de Mercado Libre

    ids_concatenados = ''
           
    nick_name = settings.NICK_NAME
    url = "https://api.mercadolibre.com/sites/MLA/search?nickname=" + str(nick_name)
            
    access_token = meli_get_authorization_code(settings.CLIENTE_ID)
    
    payload = {}
    headers = {
        'Authorization': access_token #'APP_USR-5374552499309003-040715-531af5500eba214cfed3597ccc74e677-4388206'
    }
    
    
    #Busco todos los productos del vendedor
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code==200 : 
        response_json = json.loads(response.text) #Diccionario
        articulos = response_json
        # Obtener la lista de IDs
        ids = [result['id'] for result in articulos['results']]
        # Concatenar los IDs en un solo string, separados por comas
        ids_concatenados = ','.join(ids)
    else:
        ids_concatenados=''
        messages.error(request,"Error de conexion  en Mercado Libre. - Consulta Productos")
        print("ERROR DE CONEXION - Consulta")

    return ids_concatenados

def meli_ventas(request):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CONFIG ML')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    
    if accesousuario.codigo.codigo =='CONFIG ML':

        print("Mis Ventas")
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
        
        # Busca los detalles de los artículos
        seller_id = settings.SELLER_ID

        url = "https://api.mercadolibre.com/orders/search?seller=" + str(seller_id)
        
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        
        payload = {}
        headers = {
            'Authorization': access_token #'APP_USR-710125811010660-102410-fc5f755c5fbdf1b370dd274c57b7e838-1998248263'
        }

        ventas=[]
        detail_response = requests.request("GET", url, headers=headers, data=payload)
        
        if detail_response.status_code == 200:
            ventas = detail_response.json()  # Detalles de los artículos
            # Realizar el cálculo de (total_paid_amount - (quantity * sale_fee)) para cada venta
            for venta in ventas['results']:
                total_paid_amount = venta['payments'][0]['total_paid_amount']
                shipping_cost = venta['payments'][0]['shipping_cost']
                quantity = venta['order_items'][0]['quantity']
                sale_fee = venta['order_items'][0]['sale_fee']

                # Realizar el cálculo
                venta['total_comision'] =  (quantity * sale_fee)
                venta['total_calculado'] = total_paid_amount - (quantity * sale_fee) - shipping_cost 



        else:
            print(f"Error al obtener los detalles de los productos: {detail_response.status_code}")
            print(f"Contenido de la respuesta: {detail_response.text}")
            messages.error(request, f"Error en la conexión con Mercado Libre - Detalle Productos ({detail_response.status_code})")

        
        context = {
            'permisousuario':permisousuario,
            'ventas':ventas
        }

        return render(request,'meli/meli_ventas.html',context) 

    return render(request,'panel/login.html',)