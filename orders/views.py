from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem,CartItemKit
from store.models import ProductKit
from orders.models import OrderProductKitItem
from .forms import OrderForm
import datetime
import time
from .models import Order, Payment, OrderProduct,OrigenVenta
from accounts.models import AccountDirecciones, Account
from django.db.models import F


import json
from store.models import Product,Costo


from django.template.loader import render_to_string

from api.views import enviar_whatsapp

from django.conf import settings
import smtplib
#from email.message import EmailMessage
from django.core.mail import EmailMessage
from django.db import transaction

#import pywhatkit  #Kit de envio de whatsapp

def payments(request):
    body = json.loads(request.body)
    
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True

        orderproduct.descuento_unitario = 0
        orderproduct.precio_unitario_cobrado =  item.product.price

        costo = costo_producto(item.product_id)
        
        orderproduct.costo = costo
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = 'Gracias por tu compra!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()
   

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)

def place_order(request, total=0, quantity=0,):
    current_user = request.user
    
    print("place_order:")
    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    
    if cart_count <= 0:
        return redirect('store')

    

    if request.method == 'POST':
        
        form = OrderForm(request.POST)

        canal_venta= settings.STORE_DEF_CANAL  #WEB
        origen_venta = OrigenVenta.objects.filter(codigo=canal_venta).first()
        #if origen_venta:
        #    id_origen_venta =  origen_venta.id
        #else:
        #    id_origen_venta = 1    
        
        if form.is_valid():

            envio = form.cleaned_data['envio']
            print("Costo de envio:",  envio)
            total = total if total is not None else 0.0
            envio = envio if envio is not None else 0.0
            order_total_descuentos = 0
            grand_total = 0
            for cart_item in cart_items:
                total += (cart_item.precio_real * cart_item.quantity)
                order_total_descuentos += (cart_item.desc_unit * cart_item.quantity) 
                quantity += cart_item.quantity
            
            grand_total = total + envio - order_total_descuentos
            

            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            
            data.origen_venta = origen_venta
            data.order_total_comisiones = 0
            data.order_total_impuestos = 0
            data.order_total_descuentos = order_total_descuentos

            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.dir_telefono = form.cleaned_data['dir_telefono']
            data.email = form.cleaned_data['email']
            data.dir_calle = form.cleaned_data['dir_calle']
            data.dir_nro = form.cleaned_data['dir_nro']
            data.dir_piso = form.cleaned_data['dir_piso']            
            data.dir_depto = form.cleaned_data['dir_depto']
            data.dir_localidad = form.cleaned_data['dir_localidad']
            data.dir_provincia = form.cleaned_data['dir_provincia']
            data.dir_cp = form.cleaned_data['dir_cp']
            data.dir_tipocorreo =  form.cleaned_data['dir_tipocorreo']
            data.dir_tipoenvio =  form.cleaned_data['dir_tipoenvio']
            data.dir_correo =  form.cleaned_data['dir_correo']
            data.dir_nombre =  form.cleaned_data['dir_nombre']
            data.envio = form.cleaned_data['envio']
            data.order_note = form.cleaned_data['dir_obs']
            data.order_total = grand_total
            data.envio = envio
            data.fecha = datetime.date.today()  #Grabo la fecha del momento
            data.ip = request.META.get('REMOTE_ADDR')
            
            print("data.dir_nombre",data.dir_nombre)
            data.save()

            
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'envio': envio,
                'order_total_descuentos':order_total_descuentos,
                'grand_total': grand_total,
            }
            print("order",order)
            return render(request, 'orders/payments.html', context)
        else:
            print("Form is not valid")
            #'first_name', 'last_name', 'dir_telefono', 'email', 'dir_calle', 'dir_nro', 'dir_localidad', 'dir_provincia', 'dir_cp','dir_obs','dir_tipocorreo','dir_tipoenvio','dir_nombre','dir_correo
            print(form)
            return redirect('store')
    else:
        print("invalid Form")
        return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    descuentos=0
    print("order_complete")
    try:
        print("try ...order_complete")
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.precio_unitario_cobrado * i.quantity
            descuentos += i.descuento_unitario * i.quantity 
            
    
        payment = Payment.objects.get(payment_id=transID)
        print("Descuentos",descuentos)
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'descuentos':descuentos,
        }
        return render(request, 'orders/order_complete.html', context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

def order_cash(request):
              
    if request.method =="POST":
        
        order_number = request.POST.get('order_number')
         
        pesoarticulos=0
        resultado_final = []

        order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
        
        # Move the cart items to Order Product table
        cart_items = CartItem.objects.filter(user=request.user)

        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True

            orderproduct.descuento_unitario = item.desc_unit
            orderproduct.precio_unitario_cobrado =  item.precio_con_desc
            
            costo = costo_producto(item.product_id)
            orderproduct.costo = round(costo,2)
            orderproduct.save()
            
            
            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()


            print("Item Kits")
            # Verifico los articulos KITS y sus componenetes
            item_kits = CartItemKit.objects.filter(cart=cart_item)
            if item_kits:
                for item_kit in item_kits:
                   #Guardo en OrderProductKits
                    OrderProductKitItem.objects.create(order_product=orderproduct, product=item_kit.product, quantity=item_kit.quantity)
                    # Redusco Stock de los articulos Kits
                    product = Product.objects.get(id=item_kit.product.id)
                    if product:
                        #pesoarticulos += product.peso * item.quantity 
                        product.stock = product.stock - item_kit.quantity
                        product.save()

            #Envio detalle de kits al order_recibe para el mail.
            kits = OrderProductKitItem.objects.filter(order_product=orderproduct).annotate(
                product_name=F('product__product_name')
                ).values('product_name', 'quantity','order_product')  # Selecciona solo el nombre del producto y la cantidad

            # Agregar al resultado final
            resultado_final.extend(list(kits))  # Convierte el queryset en lista y la extiende    


     
            print(" Fin Item Kits")
            # Reduce el stock del articulo KIT original
            product = Product.objects.get(id=item.product_id)
            if product:
                pesoarticulos += product.peso * item.quantity 
                product.stock = product.stock - item.quantity
                product.save()

              
                        
            
        #print("total peso Articulos:",pesoarticulos)
        # Clear cart
        CartItem.objects.filter(user=request.user).delete()

        # *************************
        # ORDER COMPLETE
        #**************************
        try:

            if order:
                order.is_ordered = True  #Confirmo la orden de compa
                order.total_peso = pesoarticulos
                user = Account.objects.filter(email=order.user).first()
                
                #order.dir_nombre = ""
                order.save()

            print("order status", order.is_ordered)

            order = Order.objects.get(order_number=order_number, is_ordered=True)
            ordered_products = OrderProduct.objects.filter(order_id=order.id).annotate(
                    subtotal_line=F('quantity') * F('precio_unitario_cobrado'),
                    total_discount=F('descuento_unitario') * F('quantity')
                )

            subtotal = 0
            descuentos=0
            for i in ordered_products:
                subtotal += i.product_price * i.quantity
                descuentos += i.descuento_unitario * i.quantity 
                

            #Es pago contra recibo
            #payment = Payment.objects.get(payment_id=transID)
            payment = []
            print("descuentos",descuentos)


            #*************************************
            # SEND EMAIL
            #**************************************

            # Send order recieved email to customer
            mail_subject = 'Gracias por tu compra!!'
            message = render_to_string('orders/order_recieved_email.html', {
                'user': request.user,
                'order': order,
                'ordered_products': ordered_products,
                'products_and_quantities':resultado_final,
                'order_number': order.order_number,
                'transID': 'Pendiente', #payment.payment_id,
                'payment': payment,    #Viaja Vacío
                'subtotal': subtotal,
                'descuentos':descuentos,
                })
            to_email =  request.user.email
            cc_email =  settings.DEF_CC_MAIL  #'lifche.argentina@gmail.com' #santidebony@hotmail.com
            
            print(to_email,cc_email)
            send_email = EmailMessage(mail_subject, message, to=[to_email],cc=[cc_email])
            send_email.content_subtype = "html"
            #send_email.attach_file('static/images/logo.png')
            send_email.send()


            #************************
            #Send Whatsapp
            #*************************
            celular=settings.DEF_CEL

            enviar_whatsapp (request,order.order_number,celular)
            print("enviar whatsapp")
            
            context = {
                'order': order,
                'ordered_products': ordered_products,
                'order_number': order.order_number,
                'transID': 'Pendiente', #payment.payment_id,
                'payment': payment,    #Viaja Vacío
                'subtotal': subtotal,
                'descuentos':descuentos,
            }
            print("Order Complete")
            return render(request, 'orders/order_complete.html', context)
    
        except (Order.DoesNotExist):
            print("Except")
            return redirect('home')

def costo_producto(product_id):

        product = Product.objects.get(id=product_id)
        if product:
            #costo = Costo.objects.filter(producto=product).order_by('-fecha_actualizacion').first()
            #if costo:
            return product.costo_prod
        else:
             return 0