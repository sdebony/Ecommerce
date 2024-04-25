
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

    authorization_code = meli_params.objects.filter(client_id=client_id).first()
    
    if not authorization_code:
        access_token = ""   
        print("ERROR: meli_get_authorization_code")
        
    
    else:
        access_token = authorization_code.access_token
        
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
                   return redirect('panel')
                      
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
        
        print("Sin Acceso ML")
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

            if request.method =="POST":
            
                code = request.POST.get("code")
                if code:
                    cliente_id = settings.CLIENTE_ID
                    print(cliente_id)
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
                        messages.success(request,"Token guardado con exito.")
                    else:
                        messages.warning(request,"No se ha podido obtener el codigo de autorizacion.")

                    print("code:",code)
                else:
                    print("Sin code")
            
                return redirect('panel')
            else:

                return render(request,'meli/meli_config.html',context)  
    

    else:
        return render(request,'panel/login.html',)

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

            refresh_token = meli_params.objects.get(client_id=cliente_id)
            if refresh_token:     
                refresh_token = meli_params(
                id = refresh_token.id,
                client_id = cliente_id,
                code = refresh_token.code,
                refresh_token = refreshtoken,
                access_token= access_token,
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
                #print("***********************")
                #print(articulos)
                #print("**********************")
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

