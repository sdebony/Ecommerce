from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile,AccountDirecciones
from django.contrib import messages

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

    # If the user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            quantity = request.POST.get("quantity")
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
              
                if quantity:
                    #print("articulo existe...")
                    if item.quantity == int(quantity):
                        #print("Si la cantidad ingresada es igual a la que tiene suma 1")
                        item.quantity += 1
                    else:
                        item.quantity = int(quantity)  #Modifico desde Cart cantidad
                else:
                    item.quantity += 1
                item.save()

            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            if not quantity:
                print("quantity=1 (null)")
                quantity = 1
            else:
                print("quantity=",quantity)
                quantity = int(quantity)

            cart_item = CartItem.objects.create(
                product = product,
                quantity = quantity, #1 inicial
                user = current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
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

            print(ex_var_list)

            if product_variation in  ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
               

                if quantity==None:
                    quantity=1

                if quantity:
                    if item.quantity == int(quantity):
                        item.quantity += 1
                    else:
                        item.quantity = int(quantity)
                else:
                    item.quantity += 1
                item.save()
               

            else:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            if not quantity:
                quantity = 1

            cart_item = CartItem.objects.create(
                product = product,
                quantity = int(quantity),
                cart = cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            #messages.success(request, 'Producto agregado')
            cart_item.save()

       
        if volver_store=="0":
            return redirect('cart')
        else:
            
            return redirect(ruta + "#" + str(product_id))

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
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        
        grand_total = total + envio
    except ObjectDoesNotExist:
        pass #just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'envio'       : envio,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        print("Checkout")
        envio = 0
        grand_total = 0
        if request.user.is_authenticated:
            userprofile = get_object_or_404(UserProfile, user=request.user)
            direccion = AccountDirecciones.objects.filter(user=request.user)
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        envio = 0 #(2 * total)/100
        grand_total = total + envio
    except ObjectDoesNotExist:
        pass #just ignore
    
    print("Total:",grand_total)
    if grand_total > settings.MONTO_MINIMO:
    
        context = {
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
            'envio'       : envio,
            'grand_total': grand_total,
            'userprofile': userprofile,
            'direccion' :direccion,
        }
        return render(request, 'store/checkout.html', context)
    else:
        messages.error(request, 'El mìnimo de compras mayoristas es de: $'+ str(settings.MONTO_MINIMO))
        return redirect('cart')
