
from django.shortcuts import render, get_object_or_404,redirect
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import AccountPermition,UserProfile,Account,BillingInfo
from meli.models import meli_params
from django.contrib import messages
from orders.models import Order, OrderProduct,Payment,OrigenVenta,Product
from contabilidad.models import ConfiguracionParametros



from datetime import datetime
from datetime import date
from django.db.models import Q

import requests
from django.http import JsonResponse
import json
# Create your views here.

from django.conf import settings

def meli_get_authorization_code(client_id):


    #print("meli_get_authorization_code. Cliente ID:", client_id)
    authorization_code = meli_params.objects.filter(client_id=client_id).first()
    
    if not authorization_code:
        access_token = ""   
        print("ERROR: meli_get_authorization_code")
        
    
    else:
        access_token = authorization_code.access_token
        #print("Tomo el access token de la base:",access_token)
    
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

                    messages.success(request,"Token guardado con exito.",str(token.access_token))
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
                    messages.success(request,"REFRESH TOKEN  guardado con exito.:" + str(access_token))
                
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

        # Obtener todas las publicaciones
        publicaciones = meli_get_all_publicaciones(request)

        # Divide las publicaciones en chunks de máximo 20
        publicaciones_lista = publicaciones.split(',')
        chunk_size = 20
        publicaciones_chunks = [publicaciones_lista[i:i + chunk_size] for i in range(0, len(publicaciones_lista), chunk_size)]

        # Calcular la cantidad total de publicaciones
        cantidad_publicaciones = len(publicaciones_lista)

        # Token de autorización
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        headers = {
            'Authorization': access_token
        }

        articulos = []

        # Iterar sobre los chunks y realizar solicitudes a la API
        for chunk in publicaciones_chunks:
            ids_concatenados = ','.join(chunk)  # Concatenar los IDs separados por comas
            url = f"https://api.mercadolibre.com/items?ids={ids_concatenados}"
            payload = {}

            detail_response = requests.request("GET", url, headers=headers, data=payload)

            if detail_response.status_code == 200:
                chunk_data = detail_response.json()  # Obtener los datos del chunk
                for item in chunk_data:
                    if 'body' in item:  # Validar que el detalle de la publicación está disponible
                        publicacion_id = item['body']['id']
                        
                        # Buscar el producto en el modelo Product
                        producto = Product.objects.filter(Q(sku_meli__regex=rf'(^|,){publicacion_id}(,|$)')).first()
                        
                       # Obtener el estado de la publicación
                        
                        respuesta = meli_get_estado_publicacion(request, publicacion_id)
                        
                        estado_publicacion = respuesta["status"]
                        precio_to_win = respuesta["price_to_win"]
                        # Si el estado es una cadena válida, úsal
                        # o; de lo contrario, asigna un valor predeterminado
                        status = estado_publicacion if estado_publicacion else 'Estado no disponible'

                        precio_sugerido = meli_calcular_comisiones(producto,precio_to_win)
                       

                        # Añadir los datos al resultado
                        articulos.append({
                            'publicacion': item['body'],
                            'producto': producto,  # Será None si no se encuentra
                            'status': status,
                            'precio_to_win':precio_to_win,
                            'ganancia_precio_competencia': precio_sugerido
                        })

                       
            else:
                print(f"Error al obtener los detalles del chunk: {detail_response.status_code}")
                print(f"Contenido de la respuesta: {detail_response.text}")
                messages.error(request, f"Error en la conexión con Mercado Libre - Detalle Productos ({detail_response.status_code})")

        # Contexto para la plantilla
        context = {
            'permisousuario': permisousuario,
            'articulos': articulos,  # Todos los resultados con información del producto
            'cantidad_publicaciones': cantidad_publicaciones  # Cantidad total de publicaciones
        }

        return render(request, 'meli/meli_publicaciones.html', context)
        

    return render(request,'panel/login.html',)

def meli_get_all_publicaciones(request):
    # Obtiene la lista de publicaciones de Mercado Libre

    ids_concatenados = ''
           
    seller_id = settings.SELLER_ID
    url = "https://api.mercadolibre.com/sites/MLA/search?seller_id=" + str(seller_id)
          
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

                total_amount = sum(payment["total_paid_amount"] for payment in venta["payments"])
               
                
                # Realizar el cálculo
                venta['total_comision'] =  (quantity * sale_fee)
                venta['total_calculado'] = total_amount - (quantity * sale_fee) - shipping_cost 
                venta['total_amount'] = total_amount

                # Verificar si el `order_id` está en la base de datos
                order_id = venta['payments'][0].get('order_id')  # Obtener el order_id del pago
                print("order_id",order_id)
                if order_id:
                    existe = Order.objects.filter(order_number=order_id).exists()
                    venta['existe_en_bd'] = existe  # Agregar esta información a la venta para usarla en la plantilla
                else:
                    venta['existe_en_bd'] = False  # Si no hay order_id, asumimos que no existe



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

def meli_ventas_detalle(request,id_pedido_meli):

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

        print("Detalle de venta:", id_pedido_meli)
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
        
        # Busca los detalles de los artículos
        seller_id = settings.SELLER_ID

        url = "https://api.mercadolibre.com/orders/search?seller=" + str(seller_id) + "&q= " + str(id_pedido_meli)

       
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        
        payload = {}
        headers = {
            'Authorization': access_token #'APP_USR-710125811010660-102410-fc5f755c5fbdf1b370dd274c57b7e838-1998248263'
        }

        ventas=[]
        detail_response = requests.request("GET", url, headers=headers, data=payload)
        
        if detail_response.status_code == 200:
            data = detail_response.json()  # Detalles de los artículos
           
            
            # Extraer datos de `payments`
            payments = data["results"][0]["payments"]
            for payment in payments:
                total_paid_amount = payment["total_paid_amount"]
                order_id = payment["order_id"]
                transaction_amount = payment["transaction_amount"]
                # Transformar `date_approved` al formato `dd.mm-yyyy`
                date_approved_raw = payment["date_approved"]
                date_approved = datetime.fromisoformat(date_approved_raw).strftime("%d.%m-%Y")
                
            
                
            # Extraer datos de `order_items`
            order_items = data["results"][0]["order_items"]
            for item in order_items:
                item_id = item["item"]["id"]
                item_title = item["item"]["title"]
                quantity = item["quantity"]
                unit_price = item["unit_price"] - item["sale_fee"]
                full_unit_price = item["full_unit_price"]
                sale_fee = item["sale_fee"]
                

            buyer = data["results"][0]["buyer"]
            seller = data["results"][0]["seller"]
            shipping = data["results"][0]["shipping"]

            

            buyer_nickname = buyer["nickname"]
            seller_id = seller["id"]
            seller_nickname = seller["nickname"]

            #print("\nOrder ID:", order_id)
            #print("Buyer Nickname:", buyer_nickname)
            #print("Seller ID:", seller_id)
            #print("Seller Nickname:", seller_nickname)
            #print("shipping",shipping)

        else:
            print(f"Error al obtener los detalles de los productos: {detail_response.status_code}")
            print(f"Contenido de la respuesta: {detail_response.text}")
            messages.error(request, f"Error en la conexión con Mercado Libre - Detalle Productos ({detail_response.status_code})")

        
        context = {
            'permisousuario':permisousuario,
            'ventas':data
        }

        return render(request,'meli/meli_venta_detalle.html',context) 

    return render(request,'panel/login.html',)

def get_producto_ml(producto_ml, item_title):

        #producto_ml = MLA1936714068

        item_title = item_title.replace("Color Amarillo", "").replace("Tubo De Pelotas", "").strip()
        item_title = item_title.replace("Paddel", "Padel")
        product = Product.objects.filter(Q(sku_meli__regex=rf'(^|,){producto_ml}(,|$)')).first()

        if not product:
            product = Product.objects.filter(product_name__icontains=item_title).first()

        if not product:
            print("Articulo ML no encontrado")
        else:
            print("get_producto_ml:", product)
        return product
        
def importar_pedido_meli(request):
    
    if request.method == 'POST':
        # Datos del encabezado
        total_paid_amount = request.POST.get('total_paid_amount')
        transaction_amount = request.POST.get('transaction_amount')
        date_approved = request.POST.get('date_approved')
        order_id = request.POST.get('order_id')
        buyer_nickname = request.POST.get('buyer_nickname')
        seller_nickname = request.POST.get('seller_nickname')
        shipping = request.POST.get('shipping_id')
        
        print("Encabezado:",order_id,total_paid_amount,transaction_amount,date_approved,buyer_nickname,seller_nickname,shipping)
        
        
        # Procesar los detalles del pedido
        items = []
        error_items = 0
        sum_total_tax=0
        item_count = len([key for key in request.POST.keys() if key.startswith('items_item_id_')])

        for i in range(item_count):
            # Convertir a valores numéricos antes del cálculo
            quantity = int(request.POST.get(f'items_quantity_{i}', 0))
            sale_fee = float(request.POST.get(f'items_sale_fee_{i}', 0.0))

            # Calcular el total de impuestos
            total_tax = quantity * sale_fee

            item = {
                'item_id': request.POST.get(f'items_item_id_{i}'),
                'item_title': request.POST.get(f'items_item_title_{i}'),
                'quantity': request.POST.get(f'items_quantity_{i}'),
                'unit_price': request.POST.get(f'items_unit_price_{i}'),
                'full_unit_price': request.POST.get(f'items_full_unit_price_{i}'),
                'sale_fee': request.POST.get(f'items_sale_fee_{i}'),
                'total_tax': total_tax,  
            }
            items.append(item)
            sum_total_tax = float(sum_total_tax) + float(total_tax)

        
        print("order ID",order_id)

        impuestos = 0 # REvisar. round(float(total_paid_amount) * 0.08, 2)

        # Store transaction details inside Payment model
        payment = Payment(
            user = request.user,
            payment_id = "Mercado Electronico",
            payment_method = "Mercado Libre",
            amount_paid = transaction_amount,
            status = "New",
        )
        payment.save()

              
        origen_venta = OrigenVenta.objects.filter(codigo="MELI").first()

        traer_datos_shipping(request,shipping)
        
        tracking_number = request.session.get('tracking_number')
        city_name = request.session.get('city_name')
        street_name = request.session.get('street_name')
        state_name = request.session.get('state_name')
        street_number = request.session.get('street_number')
        zip_code = request.session.get('zip_code')
        receiver_name = request.session.get('receiver_name')

        if not tracking_number:
            tracking_number = '0'
        print("Datos de Entrega:",tracking_number,city_name,street_name,street_number,state_name,zip_code,receiver_name)

        traer_datos_facturacion(request,order_id)

        first_name = request.session['first_name']
        last_name = request.session['last_name']
       
        print(first_name,last_name)
        # Borrar datos de la sesión
        del request.session['first_name']
        del request.session['last_name']


        # Busca si ya existe una orden con el mismo número
        existing_order = Order.objects.filter(order_number=order_id).first()
        # Valida la condición
        if not existing_order or existing_order.status == "New":

            order, created = Order.objects.update_or_create(
                order_number=order_id,
                defaults={
                    'payment': payment,
                    'is_ordered': True,
                    'first_name' : first_name, #buyer_nickname,
                    'last_name': last_name,
                    'fecha' : datetime.fromisoformat(date_approved).strftime("%Y-%m-%d"),
                    'origen_venta' : origen_venta,
                    'dir_nombre' : "Entrega mercado Libre",
                    'dir_calle' : street_name,
                    'dir_nro': street_number,
                    'dir_localidad' :state_name,
                    'dir_provincia' :city_name,
                    'dir_cp' :zip_code,
                    'dir_obs' : 'Mercado Libre',
                    'dir_tipocorreo' : 0,
                    'dir_tipoenvio' :0,
                    'dir_correo' :0,
                    'order_total' :  round(float(transaction_amount) - float(impuestos) - float(sum_total_tax),2),
                    'order_total_comisiones' : round(float(sum_total_tax),2),
                    'order_total_impuestos' : round(float(impuestos),2),
                    'status' : "New",
                    'ip' : request.META.get('REMOTE_ADDR'),
                    'is_ordered' : True,
                    'created_at' :  datetime.fromisoformat(date_approved).strftime("%Y-%m-%d"),
                    'updated_at' : date.today(),
                    'total_peso' : 0,
                    'cuenta'  : settings.ID_CUENTA_MELI,
                    'fecha_tracking' : date.today(),
                    'nro_tracking' : tracking_number,
                    # Agrega los campos que deseas actualizar
                }
            )

            
            user = Account.objects.filter(email=request.user).first()
            try:
                OrderProduct.objects.filter(order=order).delete()
            except Order.DoesNotExist:
                print("No hay productos")

            for item_data in items:
                item_id = item_data.get('item_id')
                item_title = item_data.get('item_title')
                quantity = item_data.get('quantity')
                unit_price = item_data.get('unit_price')
                full_unit_price = item_data.get('full_unit_price')
                sale_fee = item_data.get('sale_fee')
                
                print("Items:",item_title,item_id,quantity,unit_price,full_unit_price,sale_fee)
                peso_total = 0
            
                product = get_producto_ml(item_id,item_title)
                if product:
                    peso_total = peso_total + product.peso
                    orderproduct = OrderProduct()
                    orderproduct.order = order
                    orderproduct.user = user
                    orderproduct.product = product
                    orderproduct.quantity = quantity
                    orderproduct.product_price = round(float(unit_price),2)
                    orderproduct.ordered = True
                    orderproduct.descuento_unitario = 0
                    orderproduct.precio_unitario_cobrado =  round(float(unit_price) - float(sale_fee),2) #Comision
                    orderproduct.costo = product.costo_prod
                
                    orderproduct.save()

                    #Descuento Stock producto
                    productos = Product.objects.get(id=product.id)
                    if productos:
                        product.stock = productos.stock - int(quantity)
                        product.save()

                        
                else:
                    error_items = 1
                    print("Producto no encontrado:", item_title)    
                

            order, created = Order.objects.update_or_create(
                order_number=order_id,
                defaults={
                    'total_peso' : peso_total,
                    'email': request.user.email
                        }
                
            )

            if error_items==1:
                try:
                    order = Order.objects.get(order_number=order_id)
                    order.delete()
                except Order.DoesNotExist:
                    print("La orden no existe y no se puede eliminar.")
                messages.error(request, f"Producto ML no relacionado.")
            else:
                messages.error(request, f"Pedido ingresado con éxito")
        else:
            messages.error(request, f"La orden existe pero ya fue cobrada. Deberá eliminar el pago para poder actualizarla")
        
        
       



         

    return redirect('meli_ventas')

def traer_datos_shipping(request,shipping_id):

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

        print("Shipping:", shipping_id)
        
        
        url = "https://api.mercadolibre.com/shipments/" + str(shipping_id)

       
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        
        payload = {}
        headers = {
            'Authorization': access_token #'APP_USR-710125811010660-102410-fc5f755c5fbdf1b370dd274c57b7e838-1998248263'
        }

       
        detail_response = requests.request("GET", url, headers=headers, data=payload)
        
        if detail_response.status_code == 200:
            data = detail_response.json()  # Detalles de los artículos
            
            # Extraer los datos solicitados
            tracking_number = data.get("tracking_number")
            city_name = data["receiver_address"]["city"].get("name")
            street_name = data["receiver_address"].get("street_name")
            state_name = data["receiver_address"]["state"].get("name")
            street_number = data["receiver_address"].get("street_number")
            zip_code = data["receiver_address"].get("zip_code")
            receiver_name = data["receiver_address"].get("receiver_name")

            request.session['tracking_number'] = tracking_number
            request.session['city_name'] = city_name
            request.session['street_name'] = street_name
            request.session['state_name'] = state_name
            request.session['street_number'] =street_number
            request.session['zip_code'] = zip_code
            request.session['receiver_name'] = receiver_name

            return JsonResponse({'status': 'success', 'message': 'Datos guardados correctamente'})
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def traer_datos_facturacion(request,orderid):

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

        print("Shipping:", orderid)
        
        
        url = "https://api.mercadolibre.com/orders/" + str(orderid) +  "/billing_info" 

       
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        
        payload = {}
        headers = {
            'Authorization': access_token,'x-version': '2' #'APP_USR-710125811010660-102410-fc5f755c5fbdf1b370dd274c57b7e838-1998248263'
        }

       
        detail_response = requests.request("GET", url, headers=headers, data=payload)
        
        if detail_response.status_code == 200:
            data = detail_response.json()  # Detalles de los artículos
            
            billing_info = data["buyer"]["billing_info"]     
            # Taxes
            taxpayer_type_id = billing_info["taxes"]["taxpayer_type"]["id"]
            taxpayer_description = billing_info["taxes"]["taxpayer_type"]["description"]
            
            
            if taxpayer_type_id=='05':
                name = billing_info["name"]
                last_name = billing_info["last_name"]

            if taxpayer_type_id=='07' or taxpayer_type_id == '01': #Monotributo / Resp Insc
                name = billing_info["name"]
                last_name = "EMPRESA"

            # Identification
            identification_type = billing_info["identification"]["type"]
            identification_number = billing_info["identification"]["number"]

            

            # Address
            address = billing_info["address"]
            street_name = address["street_name"]
            street_number = address["street_number"]
            city_name = address["city_name"]
            state_code = address["state"]["code"]
            state_name = address["state"]["name"]
            zip_code = address["zip_code"]
            country_id = address["country_id"]

            # Guardar en la base de datos
            billing_info, created = BillingInfo.objects.update_or_create(
                order = orderid,
                name=name,
                last_name=last_name,
                identification_type=identification_type,
                identification_number=identification_number,
                taxpayer_type_id=taxpayer_type_id,
                taxpayer_type_description=taxpayer_description,
                street_name=street_name,
                street_number=street_number,
                city_name=city_name,
                state_code=state_code,
                state_name=state_name,
                zip_code=zip_code,
                country_id=country_id,
            )


            request.session['first_name'] = name
            request.session['last_name'] = last_name
            
            return JsonResponse({'status': 'success', 'message': 'Datos guardados correctamente'})
            
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def meli_analisis_publicaciones(request,idpublicacion):

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

        # Token de autorización
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        headers = {
            'Authorization': access_token
        }

        articulos = []

        url = "https://api.mercadolibre.com/items/" + str(idpublicacion.strip()) + "/price_to_win?version=v2"
        payload = {}
        
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()
        
        # Procesa los datos para enviarlos al HTML
        articulos = {
            "item_id": data.get("item_id"),
            "current_price": data.get("current_price"),
            "currency_id": data.get("currency_id"),
            "price_to_win": data.get("price_to_win"),
            "boosts": data.get("boosts", []),
            "status": data.get("status"),
            "winner": data.get("winner", {})
        }
        

        
        # Contexto para la plantilla
        context = {
            'permisousuario': permisousuario,
            'product': articulos,  # Todos los resultados con información del producto
        }

        return render(request, 'meli/meli_analisis_publicaciones.html', context)
        

    return render(request,'panel/login.html',)

def meli_get_estado_publicacion(request,idpublicacion):

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

        # Token de autorización
        access_token = meli_get_authorization_code(settings.CLIENTE_ID)
        headers = {
            'Authorization': access_token
        }

        articulos = []

        url = "https://api.mercadolibre.com/items/" + str(idpublicacion.strip()) + "/price_to_win?version=v2"
        payload = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()
        
        # Procesa los datos para enviarlos al HTML
        articulos = {
            "item_id": data.get("item_id"),
            "current_price": data.get("current_price"),
            "currency_id": data.get("currency_id"),
            "price_to_win": data.get("price_to_win"),
            "boosts": data.get("boosts", []),
            "status": data.get("status"),
            "winner": data.get("winner", {})
        }
        
       
              
        if articulos:
            return {"status": articulos["status"], "price_to_win": articulos["price_to_win"]}
        else:    
             return {"status": "", "price_to_win": ""}
        

    return render(request,'panel/login.html',)

def meli_calcular_comisiones(idproducto, precio_competencia):


    if precio_competencia is not None:
    
    
        #COMISIONES DE VENTA  3 (Mercado Libre)
        comision3 = ConfiguracionParametros.objects.get(codigo='COM3')
        if comision3:
            com3 = comision3.valor
        else:
            com3 = 0

        
        #COSTO FIJO x VENTA ML
        costo3_menor = ConfiguracionParametros.objects.get(codigo='CST3_1') # Monte menor a 12000
        if costo3_menor:
            costo_menor = costo3_menor.valor
        else:
            costo_menor = 0

        costo3_mayor = ConfiguracionParametros.objects.get(codigo='CST3_2') # Monto mayor a 12000
        if costo3_mayor:
            costo_mayor = costo3_mayor.valor
        else:
            costo_mayor = 0

        precio_sugerido=0
        costo_fijo = 0

        if precio_competencia >= 12000:
            costo_fijo = costo_mayor
        else:
            costo_fijo = costo_menor
        
        impuesto = float(precio_competencia) * 0.06

         #Calculo el valor
        precio_sugerido = float(precio_competencia) - round(float(precio_competencia) * float(com3) / 100,2)  - costo_fijo - float(impuesto)
        product_cost = Product.objects.get(id=idproducto.id)
        if product_cost:
            costo_producto = product_cost.costo_prod
        else:
            costo_producto = 0

        return(round( precio_sugerido-costo_producto ,2))
    else:
        return(0)
