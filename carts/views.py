from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation,ProductKitEnc
from .models import Cart, CartItem,CartItemKit,CartItemDescuento
from store.models import ProductKit,ReglaDescuento
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile,AccountDirecciones
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F
import json
from datetime import datetime
# Create your views here.
from django.conf import settings


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):

    current_user = request.user
    product = Product.objects.get(id=product_id) #get the product
    quantity=0
    volver_store=0 # Volver a la pagina Store 1 = Si / 0 = No 
    ruta='store'
    sumar='SI'
    ruta = request.POST.get("ruta")
    product_info = product.product_name

     # If the user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
           
            product_id = request.POST.get('productId')
            quantity = request.POST.get('quantity')
            cantidad = request.POST.get('cantidad')
            sumar = request.POST.get('sumar','SI')
            
            print(f"Producto: {product_id}, quantity: {quantity}, cantidad: {cantidad}, sumar: {sumar}")
            try:
                if request.content_type == 'application/json':
                    # Parsear el cuerpo JSON de la solicitud
                    data = json.loads(request.body)
                    # Aquí data es una lista de diccionarios [{productId: 1, quantity: 3}, ...]
                    # Iterar sobre los productos enviados
                    for item in data:
                        product_id = item.get('productId')
                        quantity = item.get('quantity')
                        cantidad = item.get('cantidad')
                        sumar = item.get('sumar')
                        # Procesa cada producto y cantidad según tus necesidades
                        print(f"Producto: {product_id}, quantity: {quantity}, cantidad: {cantidad}")
            except json.JSONDecodeError:
                #return JsonResponse({'error': 'Error al procesar el JSON'}, status=400)
                   pass
                
            #if quantity:
            #    quantity = quantity.replace(",",".")
            print("Sumar cantidad:",sumar)

            volver_store = request.POST.get("volver_store")
            ruta = request.POST.get("ruta")
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
           
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        #Si ya existe el producto
        if is_cart_item_exists:
            
  
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id = []
            
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
                cart_id = item.cart
               
            
            if product_variation in ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                #print("1. cantidad:",quantity)
                if quantity:
                    #print("articulo existe...")
                    if item.quantity == float(quantity) and sumar.upper() == 'SI':
                        #print("Si la cantidad ingresada es igual a la que tiene suma 1")
                        item.quantity = float(quantity) + 1
                    else:
                        item.quantity = float(quantity)  #Modifico desde Cart cantidad
                else:
                    item.quantity = 1
                item.save()
                #messages.success(request, 'Producto agregado: (' + str(quantity) + ') x ' + product_info)
            
            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user,cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
            
            item = CartItem.objects.filter(product=product,user=current_user)
                            
            # PROCESO KIT
            if product.es_kit:
                print("1 . Procesando kits....")
                itemkit=[]
                user = request.user  # Usuario actual que realiza la solicitud
                try:
                    data = json.loads(request.body.decode('utf-8'))
                    itemkit = CartItem.objects.get(product=product, id=item_id)
                    CartItemKit.objects.filter(user=user,cart=itemkit).delete()

                    if data:
                        for item in data:
                            product_id = item.get('productId')
                            cantidad = item.get('cantidad')
                            
                            try:
                                # Busca el ProductKit
                                hijos = ProductKit.objects.get(id=product_id)
                                product_id_kit = hijos.productohijo.id

                                # Valida el ID del producto hijo
                                product_id_kit = int(product_id_kit)  # Asegúrate de que sea un entero

                                # Busca el producto relacionado
                                product_kit = Product.objects.get(id=product_id_kit)
                                
                                # Depuración
                                print(f"Producto encontrado: {product_kit.id} - {product_kit.product_name}")
                            except ProductKit.DoesNotExist:
                                return JsonResponse({'error': f"ProductKit con ID {product_id} no encontrado."}, status=400)
                            except Product.DoesNotExist:
                                return JsonResponse({'error': f"Producto con ID {product_id_kit} no encontrado."}, status=400)
                            except ValueError as e:
                                return JsonResponse({'error': f"Valor inválido: {str(e)}"}, status=400)

                        
                            print("Usuario:", user)
                            print("Producto:", product_kit)
                            print("Cantidad:", cantidad)
                            print("itemkit",itemkit)
                        
                            
                            # Crea o recupera el CartItemKit
                            cart_item_kits, created = CartItemKit.objects.get_or_create(
                                user=user,
                                product=product_kit,
                                cart=itemkit,  # Pasa la instancia de Cart
                                defaults={'quantity': cantidad}
                            )


                            print("FIN  kits")

                except:
                    pass
            
            #Calcula los descuentos por compras superiores a la regla.
            calcular_descuento_carrito(request)
            messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
           
        else:
            print("Proudcto NO EXISTE en carrito")
            item_id=""
            if not quantity:
               quantity = 1
            else:
                quantity = float(quantity)
            
            cart_item = CartItem.objects.create(
                product = product,
                quantity = quantity, #1 inicial
                user = current_user,
                precio_real = product.price,
                sub_total_linea = float(product.price) * int(quantity)

            )
            item_id = cart_item.id
            print("item_id",item_id)
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()


             # PROCESO KIT
            if product.es_kit:
                print("2 Procesando Kits")
                itemkit=[]
                user = request.user  # Usuario actual que realiza la solicitud
                try:
                    data = json.loads(request.body.decode('utf-8'))

                    itemkit = CartItem.objects.get(product=product, id=item_id)
                    CartItemKit.objects.filter(user=user,cart=itemkit).delete()

                    if data:
                        for item in data:
                            product_id = item.get('productId')
                            cantidad = item.get('cantidad')
                            
                            
                            hijos = ProductKit.objects.get(id=product_id)
                            if hijos:
                                product_id_kit = hijos.productohijo.id

                            # Verificar si el producto existe
                            print("kit Producto_id ",product_id_kit, " Cantidad: ", cantidad)
                
                            try:
                                product = Product.objects.get(id=product_id_kit)
                            except Product.DoesNotExist:
                                return JsonResponse({'error': f"Producto con ID {product_id} no encontrado."}, status=400)

                        
                        
                            cart_item, created = CartItemKit.objects.get_or_create(
                                user=user,
                                product=product,
                                cart=itemkit,
                                defaults={'quantity': cantidad}
                            )
                            print("FIN  kits")

                except:
                    pass
            
            #Aplico Descuento si corresponde
            calcular_descuento_carrito(request)
            messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
            #messages.success(request, 'Producto agregado')
        if volver_store=="0":
            return redirect('cart')
        else:
            if ruta:
                return redirect(ruta + "#" + str(product_id))
                #return redirect(ruta)
            else:
                return redirect('store')  #Detalle del pedido
            
    # If the user is not authenticated
    else:
        product_variation = []
        if request.method == 'POST':
            ruta = request.POST.get("ruta")
            product_id = request.POST.get('productId')
            quantity = request.POST.get('quantity')
            cantidad = request.POST.get('cantidad','1')
            sumar = request.POST.get('sumar','SI')
            
            print(f"Producto: {product_id}, quantity: {quantity}, cantidad: {cantidad}, sumar: {sumar}")
            try:
                # Parsear el cuerpo JSON de la solicitud
                if request.content_type == 'application/json':
                    data = json.loads(request.body)
                    # Aquí data es una lista de diccionarios [{productId: 1, quantity: 3}, ...]
                    # Iterar sobre los productos enviados
                    for item in data:
                        product_id = item.get('productId')
                        quantity = item.get('quantity')
                        cantidad = item.get('cantidad')
                        sumar = item.get('sumar')
                        # Procesa cada producto y cantidad según tus necesidades
                        print(f"Producto: {product_id}, quantity: {quantity}, cantidad: {cantidad}")
            except json.JSONDecodeError:
                #return JsonResponse({'error': 'Error al procesar el JSON'}, status=400)
                pass

            volver_store = request.POST.get("volver_store")
            
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass


        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart using the cart_id present in the session
            
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        cart.save()
        cart_id = cart.id
        #messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            
            # existing_variations -> database
            # current variation -> product_variation
            # item_id -> database
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
                cart_id = item.cart.id

            #print(ex_var_list)

            if product_variation in  ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
               
                print("4. cantidad:",quantity)
                if quantity==None:
                    quantity=1

                if quantity:
                    if item.quantity == float(quantity) and sumar.upper() == 'SI':
                        item.quantity = int(quantity) + 1  #Esto es para cuando presiona el mas
                    else:
                        item.quantity = float(quantity)
                else:
                    item.quantity = 1
                item.save()

            if product.es_kit:
                #print("3 Procesando Kits")
                # PROCESO KIT
                itemkit=[]
                user = request.user  # Usuario actual que realiza la solicitud
                #print(item_id)
                itemkit = CartItem.objects.get(product=product, id=item_id)
                try:
                    CartItemKit.objects.filter(cart=item_id).delete()
                except:
                    pass

                try:
                   data = json.loads(request.body.decode('utf-8'))
                
                   if data:
                    for item in data:
                        product_id = item.get('productId')
                        cantidad = item.get('cantidad')
                        
                        hijos = ProductKit.objects.get(id=product_id)
                        if hijos:
                            product_id_kit = hijos.productohijo.id
                            # Valida el ID del producto hijo
                            product_id_kit = int(product_id_kit)  # Asegúrate de que sea un entero

                        # Verificar si el producto existe
                        #print("kit Producto_id ",product_id_kit, " Cantidad: ", cantidad)
            
                        try:
                            product = Product.objects.get(id=product_id_kit)
                            
                        except Product.DoesNotExist:
                            return JsonResponse({'error': f"Producto con ID {product_id} no encontrado."}, status=400)
      
                 
                        cart_item, created = CartItemKit.objects.get_or_create(
                            #user=user,
                            product=product,
                            cart=itemkit,
                            defaults={'quantity': cantidad}
                        )
                        product_id = product_id_kit
                        print("FIN  kits",product_id)
                except:
                    pass        
                        
                calcular_descuento_carrito(request)      
                #messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
               
            else:
                #print("No es KIT ... Continuo")
                #item = CartItem.objects.create(product=product, quantity=1, cart=cart,precio_real = product.price,sub_total_linea = float(product.price) * int(quantity))
                item, created = CartItem.objects.get_or_create(
                    product=product,
                    cart=cart,
                    defaults={
                        'quantity': 1,
                        'precio_real': product.price,
                        'sub_total_linea': float(product.price) * int(quantity)
                    }
                )
                
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
                #messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
        else:
            #print("Producto No exiete en el cart",cart.cart_id)
            if not quantity:
                quantity = 1

            cart_item = CartItem.objects.create(
                product = product,
                quantity = int(quantity),
                cart = cart,
                precio_real = product.price,
                sub_total_linea = float(product.price) * int(quantity)
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            #messages.success(request, 'Producto agregado')
            cart_item.save()
            item_id = cart_item.id
            
            
            if product.es_kit:
                print("4 Procesando Kits")
                # PROCESO KIT
                itemkit=[]
               
                
                try:
                    data = json.loads(request.body.decode('utf-8'))
                    itemkit = CartItem.objects.get(product=product, id=item_id)
                    CartItemKit.objects.filter(cart=itemkit).delete()
                    if data:
                        
                        for item in data:
                            product_id = item.get('productId')
                            cantidad = item.get('cantidad')
                            hijos = ProductKit.objects.get(id=product_id)
                            if hijos:
                                product_id_kit = hijos.productohijo.id

                            # Verificar si el producto existe
                    
                            try:
                                product = Product.objects.get(id=product_id_kit)
                            except Product.DoesNotExist:
                                return JsonResponse({'error': f"Producto con ID {product_id} no encontrado."}, status=400)
                

                            cart_item, created = CartItemKit.objects.get_or_create(
                                product=product,
                                cart=itemkit,
                                defaults={'quantity': cantidad}
                            )
                            print("FIN  kits")
                except:
                    pass


        #Recaulcular
        calcular_descuento_carrito(request)
        messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
        
        if volver_store=="0":
            return redirect('cart')
        else:
            if ruta:
                return redirect(ruta + "#" + str(product_id))
            else:
                return redirect('cart')

def remove_cart(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

        #Recaulcular
        calcular_descuento_carrito(request)
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()

    #Recaulcular
    calcular_descuento_carrito(request)
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        envio = 0
        grand_total = 0
        descuento=0
        resultado_final = []
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            descuento += (cart_item.desc_unit * cart_item.quantity)
            quantity += cart_item.quantity
            kits = CartItemKit.objects.filter(cart=cart_item).annotate(
                product_name=F('product__product_name')
                 ).values('product_name', 'quantity','cart')  # Selecciona solo el nombre del producto y la cantidad

            # Agregar al resultado final
            resultado_final.extend(list(kits))  # Convierte el queryset en lista y la extiende    
           
        
        grand_total = total + envio - descuento
    except ObjectDoesNotExist:
        pass #just ignore

    try:
        calcular_descuento_carrito(request)
    except:
        print("EXCEPT:  Sin carrito")
        pass
    
    context = {
        'total': total,
        'descuento': descuento,
        'quantity': quantity,
        'cart_items': cart_items,
        'products_and_quantities':resultado_final,
        'envio'       : envio,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        print("Checkout")
        envio = 0
        resultado_final = []
        cart_items=[]
        grand_total = 0
        if request.user.is_authenticated:
            userprofile = get_object_or_404(UserProfile, user=request.user)
           
            direccion = AccountDirecciones.objects.filter(user=request.user)
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
       
        is_valid = validate_cart_items(cart_items)
        if is_valid:
            #Recaulcular
           
            
            calcular_descuento_carrito(request)
            print('Validación exitosa.')
        else:
            print('La validación ha fallado.')
            messages.error(request, 'Las cantidades de los productos KITs no son correctos')
            return redirect('cart')


        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
            kits = CartItemKit.objects.filter(cart=cart_item).annotate(
                product_name=F('product__product_name')  # Anota el nombre del producto
                 ).values('product_name', 'quantity','cart')  # Selecciona solo el nombre del producto y la cantidad

            # Agregar al resultado final
            resultado_final.extend(list(kits))  # Convierte el queryset en lista y la extiende    
                


     
        envio = 0 #(2 * total)/100
        grand_total = total + envio
    except ObjectDoesNotExist:
        pass #just ignore
    
    
    if grand_total > settings.MONTO_MINIMO:
    
        context = {
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
            'products_and_quantities':resultado_final,
            'envio'       : envio,
            'grand_total': grand_total,
            'userprofile': userprofile,
            'direccion' :direccion,
        }
        return render(request, 'store/checkout.html', context)
    else:
        messages.error(request, 'El mìnimo de compras mayoristas es de: $'+ str(settings.MONTO_MINIMO))
        return redirect('cart')

def validate_cart_items(cartitem_queryset):

    # Calcular la cantidad total de unidades en CartItem
    total_cartitem_units = 0
    for item in cartitem_queryset:
        product_kit = ProductKitEnc.objects.filter(productokit=item.product).first()
        if product_kit:
            total_cartitem_units += item.quantity * product_kit.cant_unidades

    # Obtener la suma de las cantidades de CartItemKit relacionadas
    cart_item_ids = cartitem_queryset.values_list('id', flat=True)
    total_cartitemkit_quantity = CartItemKit.objects.filter(cart_id__in=cart_item_ids).aggregate(
        total_quantity=Sum('quantity')
    )['total_quantity'] or 0

    # Comparar los valores
    return total_cartitem_units == total_cartitemkit_quantity

def calcular_y_guardar_descuentos(itemid):

    from store.views import obtener_mejor_descuento  # Importación local

    precio_con_desc=0
    #print("calcular_y_guardar_descuentos")
    
    item_cart = CartItem.objects.get(id=itemid)
    if item_cart:
        producto = item_cart.product
        quantity = item_cart.quantity

        descuento_unit=0
        precio_con_descuento=0
        subtotal_linea=0
        precio_prod = item_cart.product.price
        product = Product.objects.get(id=item_cart.product.id)

        # PROCESO PROMOCIONES
        descuento = obtener_mejor_descuento(producto,quantity)
        monto_descuento = descuento["descuento"]  #TOTAL
        nombre_descuento = descuento["regla_descuento"]
        porcentaje_descuento = descuento["porcenteje_descuento"]
        tipo_descuento = descuento["tipo_descuento"]
        id_regla_desc = descuento["id_regla_descuento"]
      
        # Ahora puedes usar promo y tipo_descuento como variables independientes
        #print(f"monto_descuento: {monto_descuento}, Nombre descuento: {nombre_descuento}, porcentaje_descuento: {porcentaje_descuento}, tipo_descuento: {tipo_descuento}")
       
        if monto_descuento > 0:
            #Grabo la info )
            
            regla_descuento = ReglaDescuento.objects.get(id=id_regla_desc) if id_regla_desc else None
            descuento_unit = float(monto_descuento) / int(quantity)
            descuento_total = float(monto_descuento) 

            precio_prod = product.price


            # Crear y guardar el registro
            cart_item_descuento, create = CartItemDescuento.objects.update_or_create(
                cartitemid=item_cart,
                product=product,
                defaults={
                    'quantity':int(quantity),
                    'descuento_unit':float(descuento_unit),
                    'descuento_total':float(descuento_total),
                    'porcentaje_descuento':int(porcentaje_descuento),
                    'regladescuento':regla_descuento
                    }
                )

            precio_con_descuento = float(precio_prod)- float(descuento_unit)
            subtotal_linea = float(precio_con_descuento) * int(quantity)
            # Guardar el registro en la base de datos
            cart_item_descuento.save()

        else:
            descuento_unit=0
            precio_prod = item_cart.product.price
            precio_con_descuento=precio_prod
            subtotal_linea= float(precio_con_descuento) * int(quantity)
            

        cart_item, created = CartItem.objects.update_or_create(
        id=itemid,
        product=product,
        defaults={
            'desc_unit': float(descuento_unit),
            'precio_con_desc': float(precio_con_descuento),
            'sub_total_linea': float(subtotal_linea),
            'precio_real':float(precio_prod)
            
                }
            )
      
        return {"calcular_y_guardar_descuentos": precio_con_desc}

def calcular_descuento_carrito(request):
    

    cartid = 0
    total = 0
    total_c_desc=0
    total_s_desc=0
    total_items=1
    desc_unit_tot=0
    total_cant_c_desc=0
    total_cant_s_desc=0
    descuento_total=0
    
    if not request.user.is_authenticated:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True).first()

        if cart_items:
            cartid = cart_items.cart.id
        else:
            cartid = 0

    print("calcular_descuento_carrito",cartid)

    try:
        
        # Filtrar todos los CartItems asociados al carrito
        if cartid ==0:
            cartitem = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cartitem = CartItem.objects.filter(cart=cartid)
        if cartitem.exists():
            #Elimino los descuentos
            for items in cartitem:
                # Recalcula los descuentos: elimina lo que existe
                cart_item_desc = CartItemDescuento.objects.filter(cartitemid=items.id)
                if cart_item_desc.exists():
                    cart_item_desc.delete()
                    
                #Calculo descuento individual por articulo
                #print("Linea de articulo:",items.id)
                calcular_y_guardar_descuentos(items.id)
        
            #Recalculo los descuentos
            for items in cartitem:
               
                if items.desc_unit > 0:
                    total_c_desc = float(total_c_desc) + float(items.precio_real) * int(items.quantity)
                    total_cant_c_desc = float(total_cant_c_desc) + int(items.quantity)
                    #print("total_c_desc", total_c_desc, " Cantidad afectada: ", total_cant_c_desc)
                else:
                    total_s_desc = float(total_s_desc) + float(items.precio_real) * int(items.quantity)
                    total_cant_s_desc = float(total_cant_s_desc) + int(items.quantity)
                    #print("total_s_desc", total_s_desc, " cantidad afectada: ", total_cant_s_desc)
                    
                


            ahora = datetime.now()
            # Filtrar reglas activas Y QUE TENGAN MONTOS DESDE Y HASTA
            reglas = ReglaDescuento.objects.filter(
                activo=True,
                fecha_inicio__lte=ahora,
                fecha_fin__gte=ahora,
                monto_desde__gt=0,

            )

            # Evaluar todas las reglas activas
            for regla in reglas:
                monto_desde = float(regla.monto_desde)
                monto_hasta = float(regla.monto_hasta)
                porcentaje = regla.valor_descuento
                acumulable = regla.acumulable
                total = 0
                desc_unit_tot_linea=0
                precio_con_descuento=0
                subtotal_linea=0
                
                monto_descuento=0
                #print("Reglas....",regla.nombre)
                if acumulable == True:
                    #Tomo el monto total del pedid para calcular el descuento  
                    total = total_c_desc + total_s_desc
                    total_items = total_cant_s_desc + total_cant_c_desc
                else:
                    total = total_s_desc
                    total_items = total_cant_s_desc

                if monto_desde <= float(total) <= monto_hasta:
                    monto_descuento = float(total) * float(porcentaje) / 100
                    desc_unit_tot = monto_descuento / total_items
                    #print("Aplica monto descuento")

                    #cartitem_udp = CartItem.objects.filter(cart=cartid)
                    #if cartitem_udp.exists():
                    for items in cartitem:
                        product = Product.objects.get(id=items.product.id)
                        desc_unit_tot_linea = desc_unit_tot + items.desc_unit
                        #Valido si le corresponde el descuento al articulo. Acumulable
                        if acumulable == True:
                            #Le corresponde a todos los articulos
                            quantity = items.quantity
                            descuento_total = int(quantity) * float(desc_unit_tot)
                        else:
                            if items.desc_unit == 0:  #Corresponde si no tiene descuento
                                quantity = items.quantity
                                descuento_total = int(quantity) * float(desc_unit_tot)
                            else:
                                descuento_total=0
                        
                        descuento_total=round(descuento_total,2)
                        desc_unit_tot=round(desc_unit_tot,2)

                        if descuento_total>0:
                            # Crear un nuevo registro de descuento
                            cart_item_descuento = CartItemDescuento.objects.create(
                                cartitemid=items,  # Usa el `CartItem` actual
                                product=product,
                                regladescuento=regla,
                                quantity=int(quantity),
                                descuento_unit=float(round(desc_unit_tot,2)),
                                descuento_total=float(round(descuento_total,2)),
                                porcentaje_descuento=int(porcentaje)
                            )
                            cart_item_descuento.save()


                        # Save the record (optional, as `update_or_create` already saves it)
                            

                            precio_prod = items.precio_real
                            precio_con_descuento=float(round(precio_prod,2)) - float(round(desc_unit_tot,2))
                            subtotal_linea = int(quantity) * float(precio_con_descuento)
                            subtotal_linea = round(subtotal_linea,2)
                            

                            #print("desc_unit_tot: ",desc_unit_tot)
                            #print("precio_prod: ",precio_prod)
                            #print("subtotal_linea: ",subtotal_linea)


                            
                            #Actualizo CartItem y sumo todos los descuentos.
                            # Filtrar todos los CartItems asociados al carrito
                            if cartid ==0:
                                cart_item_udp, created = CartItem.objects.update_or_create(
                                        id=items.id,
                                        product=product,
                                        user=request.user,
                                        is_active=True,
                                        defaults={
                                            'desc_unit': float(round(desc_unit_tot,2)),
                                            'precio_con_desc': float(round(precio_con_descuento,2)),
                                            'sub_total_linea': float(round(subtotal_linea,2)),
                                            'precio_real':float(precio_prod)
                                            
                                                }
                                            )
                                #print("Linea articulo actualizada - User",request.user)

                            else:
                                cart_item_udp, created = CartItem.objects.update_or_create(
                                    id=items.id,
                                    product=product,
                                    cart=cartid,
                                    is_active=True,
                                    defaults={
                                        'desc_unit': float(desc_unit_tot_linea),
                                        'precio_con_desc': float(precio_con_descuento),
                                        'sub_total_linea': float(subtotal_linea),
                                        'precio_real':float(precio_prod)
                                        
                                            }
                                        )
                                #print("Linea articulo actualizada - Cart:",cartid)

                        #else:
                            #print("No corresponde descuento")       
                #else:
                    #Si no aplica hay que eliminar el descuento en itemdescuento y actualizar items
                    #print("No Aplica monto descuento")

            #print("Sumar al monto descuento unitario de cada articulo:$", descuento_total)
            return descuento_total
        else:
            #print("Carrito sin productos")
            return 0
    except:
        #print("EXCEPT:  Sin carrito")
        pass
