from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation,ProductKitEnc
from .models import Cart, CartItem,CartItemKit
from store.models import ProductKit
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile,AccountDirecciones
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F
import json
from django.db.models import F
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
    ruta = request.POST.get("ruta")
    product_info = product.product_name

    print("add_cart")
    print(ruta)
    
     # If the user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            quantity = request.POST.get("quantity")
            if quantity:
                quantity = quantity.replace(",",".")
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
            
            if product_variation in ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                #print("1. cantidad:",quantity)
                if quantity:
                    #print("articulo existe...")
                    if item.quantity == float(quantity):
                        #print("Si la cantidad ingresada es igual a la que tiene suma 1")
                        item.quantity = float(quantity) + 1
                    else:
                        item.quantity = float(quantity)  #Modifico desde Cart cantidad
                else:
                    item.quantity = 1
                item.save()
                #messages.success(request, 'Producto agregado: (' + str(quantity) + ') x ' + product_info)
            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
            

            # PROCESO KIT
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
            messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
           
        else:
            item_id=""
            if not quantity:
               quantity = 1
            else:
                quantity = float(quantity)
            #print("2. cantidad:",quantity)
            cart_item = CartItem.objects.create(
                product = product,
                quantity = quantity, #1 inicial
                user = current_user,
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
            quantity = request.POST.get("quantity")
            #print("3. cantidad:",quantity)
            if quantity:
                quantity = quantity.replace(",",".")
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
        messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)

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

            #print(ex_var_list)

            if product_variation in  ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
               
                #print("4. cantidad:",quantity)
                if quantity==None:
                    quantity=1

                if quantity:
                    if item.quantity == float(quantity):
                        item.quantity = quantity
                    else:
                        item.quantity = float(quantity)
                else:
                    item.quantity = 1
                item.save()

            if product.es_kit:
                print("3 Procesando Kits")
                # PROCESO KIT
                itemkit=[]
                user = request.user  # Usuario actual que realiza la solicitud
                print(item_id)
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
                        print("kit Producto_id ",product_id_kit, " Cantidad: ", cantidad)
            
                        try:
                            product = Product.objects.get(id=product_id_kit)
                            
                        except Product.DoesNotExist:
                            return JsonResponse({'error': f"Producto con ID {product_id} no encontrado."}, status=400)
      
                        

                       
                        print("Usuario:", user)
                        print("Producto:", product)
                        print("Cantidad:", cantidad)
                        print("itemkit",itemkit)
                    
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
                        
                      
                messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
               
            else:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
                messages.success(request,  'Producto agregado: (' + str(quantity) + ') x ' + product_info)
        else:
            #print("5. cantidad:",quantity)
            if not quantity:
                quantity = 1

            cart_item = CartItem.objects.create(
                product = product,
                quantity = float(quantity),
                cart = cart,
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
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        envio = 0
        grand_total = 0
        resultado_final = []
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
            kits = CartItemKit.objects.filter(cart=cart_item).annotate(
                product_name=F('product__product_name')
                 ).values('product_name', 'quantity','cart')  # Selecciona solo el nombre del producto y la cantidad

            # Agregar al resultado final
            resultado_final.extend(list(kits))  # Convierte el queryset en lista y la extiende    
           
        
        grand_total = total + envio
    except ObjectDoesNotExist:
        pass #just ignore

    context = {
        'total': total,
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