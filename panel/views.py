from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from accounts.models import AccountPermition,Permition
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from store.models import Product,Variation
from orders.models import Order, OrderProduct,Payment,OrderShipping
from category.models import Category
from accounts.models import Account, UserProfile
from contabilidad.models import Cuentas, Movimientos,Operaciones, Monedas, Transferencias
from panel.models import ImportTempProduct, ImportTempOrders, ImportTempOrdersDetail

from accounts.forms import UserForm, UserProfileForm
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from slugify import slugify
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.conf import settings

import xlwt,xlrd
import csv


import os
# Create your views here.
def panel_home(request):
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PANEL')
        else:
            print("sin acceso")
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            print("exception")
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =="PANEL":
        
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        context = {
            'permisousuario':permisousuario
            }
        print("Acceso Panel")
        return render (request,"panel/base.html",context)

    print('Sin modulo PANEL')
    return render(request,'dashboard',)
    
def dashboard_ventas(request):
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='DASHBOARD VENTAS')
        else:
            print("sin acceso")
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            print("exception")
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =="DASHBOARD VENTAS":
        
        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")     
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=90) 
            fecha_desde = fecha_hasta - dias
        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')

        #print(fecha_desde,fecha_hasta)

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        saldos = Movimientos.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('cuenta__nombre').annotate(total=Sum('monto')).order_by('cuenta')
        pedidos = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('status').annotate(cantidad=Count('order_number')).order_by('status')
        
        clientes = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('last_name').annotate(total=Sum('order_total')).order_by('-order_total')[:5]
      
        hist_pedidos = []

        for i in range(1, 13): 
            payments_months = Order.objects.filter(fecha__month = i)
            month_earnings = round(sum([Order.order_total for Order in payments_months]))
            hist_pedidos.append(month_earnings)
      
        #print(clientes)

        form = []
        context = {
            'permisousuario':permisousuario,
            'hist_pedidos':hist_pedidos,
            'data': saldos,
            'pedidos':pedidos,
            'clientes':clientes,
            'form': form,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta
           
            }
        print("Acceso Panel")
        return render (request,"panel/dashboard_ventas.html",context)
    print('Sin acceso DASHBOARD VENTAS')
    return render(request,'dashboard',)

def panel_product_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PRODUCTO')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PRODUCTO':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        catalogo = Product.objects.filter().all()
        cantidad = catalogo.count()
        context = {
            'catalogo':catalogo,
            'permisousuario':permisousuario,
            'cantidad':cantidad
        }
       
        return render(request,'panel/lista_productos.html',context) 

    return render(request,'panel/login.html',)

def panel_product_detalle(request,product_id=None):
    
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PRODUCTO')
            if accesousuario:
                if accesousuario.modo_editar==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
    
    if accesousuario.codigo.codigo =='PRODUCTO':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        if product_id:
            product = get_object_or_404(Product, id=product_id)

            producto = Product.objects.get(product_name=product.product_name)
            categorias = Category.objects.all()
            variantes = Variation.objects.filter(product=product)

            
        else:
            categorias = Category.objects.all()
            producto = []
            variantes = []

        context = {
            'producto':producto,
            'permisousuario':permisousuario,
            'categorias': categorias,
            'variantes':variantes,
        }
    
        return render(request,'panel/productos_detalle.html',context) 
       
def panel_pedidos_list(request,status=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PEDIDOS':

        if not status:
            status='New'

       
        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")     
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=240) 
            fecha_desde = fecha_hasta - dias
        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')
         
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        #ordenes = Order.objects.filter(status=status).order_by('-created_at')
        ordenes = Order.objects.filter(status=status,fecha__range=[fecha_desde,fecha_hasta]).order_by('-created_at')
        cantidad = ordenes.count()
        cantidad_new = Order.objects.filter(status='New',fecha__range=[fecha_desde,fecha_hasta]).count()
        total_new = Order.objects.filter(status='New',fecha__range=[fecha_desde,fecha_hasta]).aggregate(Sum('order_total'))

        cantidad_cobrado = Order.objects.filter(status='Cobrado',fecha__range=[fecha_desde,fecha_hasta]).count()
        total_cobrado = Order.objects.filter(status='Cobrado',fecha__range=[fecha_desde,fecha_hasta]).aggregate(Sum('order_total'))

        cantidad_entregado = Order.objects.filter(status='Entregado',fecha__range=[fecha_desde,fecha_hasta]).count()
        total_entregado = Order.objects.filter(status='Entregado',fecha__range=[fecha_desde,fecha_hasta]).aggregate(Sum('order_total'))

        amount_new=total_new["order_total__sum"]
        amount_cobrado=total_cobrado["order_total__sum"]
        amount_entregado=total_entregado["order_total__sum"]

        if not amount_new:
            amount_new=0
        if not amount_cobrado:
            amount_cobrado = 0
        if not amount_entregado:
            amount_entregado = 0

        fecha_desde = fecha_desde.strftime("%d/%m/%Y")
        fecha_hasta = fecha_hasta.strftime("%d/%m/%Y")

        amount_new = round(amount_new)
        amount_cobrado = round(amount_cobrado)
        amount_entregado = round(amount_entregado)

        context = {
            'ordenes':ordenes,
            'permisousuario':permisousuario,
            'cantidad':cantidad,
            'status':status,
            "amount_new": amount_new ,
            "cantidad_new": cantidad_new,
            "amount_cobrado":amount_cobrado,
            "cantidad_cobrado":cantidad_cobrado,
            "amount_entregado":amount_entregado,
            "cantidad_entregado":cantidad_entregado,
            "fecha_desde":fecha_desde,
            "fecha_hasta":fecha_hasta
            


        }
        return render(request,'panel/lista_pedidos.html',context) 

    return render(request,'panel/login.html',)

def panel_pedidos_detalle(request,order_number=None):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PEDIDOS':
        print("Ingreso")
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        ordenes = Order.objects.get(order_number=order_number)
        ordenes_detalle = OrderProduct.objects.filter(order_id=ordenes.id)
        subtotal = ordenes.order_total - ordenes.envio
        if ordenes.status=="New":
            pago_pendiente=True
            entrega_pendinete=False
            entregado=False
        elif ordenes.status=="Cobrado":
            pago_pendiente=False
            entrega_pendinete=True
            entregado=False
        elif ordenes.status=="Entregado":
            pago_pendiente=False
            entrega_pendinete=False
            entregado=True

        print("ordenes.status",ordenes.status,pago_pendiente,subtotal)
        
        context = {
            'ordenes':ordenes,
            'permisousuario':permisousuario,
            'ordenes_detalle':ordenes_detalle,
            'subtotal': subtotal,
            'pago_pendiente': pago_pendiente,
            'entrega_pendinete':entrega_pendinete,
            'entregado':entregado
        }
        
        return render(request,'panel/pedidos_detalle.html',context) 

    return render(request,'panel/login.html',)

def panel_pedidos_eliminar(request,order_number=None):

    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PEDIDOS':
        print("Eliminar")
        if order_number:
                ordenes = Order.objects.get(order_number=order_number)
                if ordenes:
                    ordenes_detalle = OrderProduct.objects.filter(order_id=ordenes.id)
                    if ordenes_detalle:
                        ordenes_detalle.delete()
                ordenes.delete()
                messages.success(request,"Pedido eliminado con exito.")
        
        return redirect('panel_pedidos','New')

    return render(request,'panel/login.html',)

def panel_productos_variantes(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PRODUCTO')
            if accesousuario:
                if accesousuario.modo_editar==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
    
    if accesousuario.codigo.codigo =='PRODUCTO':

        if request.method =="POST":

            product_id = request.POST.get("product_id")
            variation_category = request.POST.get("variation_category")
            variation_value = request.POST.get("variation_value")
           
            product = get_object_or_404(Product, id=product_id)
            vari = Variation.objects.filter(product=product,variation_category=variation_category,variation_value=variation_value)

            if not vari:
                

                vari = Variation(
                    product=product,
                    variation_category=variation_category,
                    variation_value=variation_value,
                    is_active=True,
                    created_date=datetime.today(),
                )
                vari.save()
            
            return redirect('panel_producto_detalle', str(product_id)) 

def panel_productos_variantes_del(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PRODUCTO')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
    
    if accesousuario.codigo.codigo =='PRODUCTO':

        if request.method =="POST":

            var_id = request.POST.get("var_id")
            product_id = request.POST.get("product_id")
            print("panel_productos_variantes_del")
            print(var_id)
            
            vari = Variation.objects.filter(id=var_id)

            if vari:
                vari.delete()
            
            return redirect('panel_producto_detalle', str(product_id)) 

def panel_product_crud(request):
    
    try:
        
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user.id, codigo__codigo ='PRODUCTO')  
            if accesousuario:
                if accesousuario.modo_editar==False:
                    return render(request,'panel/login.html',)     
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Validar Acceso
    
    if accesousuario.codigo.codigo =='PRODUCTO':

        if request.method =="GET":
            #ALTA
            print("GET ")
            categorias = Category.objects.all()
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            producto = []
            variantes = []

            context = {
                'producto':producto,
                'permisousuario':permisousuario,
                'categorias': categorias,
                'variantes':variantes,
            }
        
            return render(request,'panel/productos_detalle.html',context) 

        if request.method =="POST":
            
            
            
            product_id = request.POST.get("product_id")
            product_name = request.POST.get("product_name")
            description = request.POST.get("description")
            habilitado = request.POST.getlist("is_available[]")
            price = request.POST.get("price")
            images = request.POST.get("images")
            stock = request.POST.get("stock")
            cat_id = request.POST.get("category")
           
            category = Category.objects.get(id=cat_id)
         
            if product_id:
                producto = Product.objects.filter(id=product_id).first()
                created_date = producto.created_date
                
                if not images:
                    images = "photos/products/none.jpg" #default      
                else:
                    images = producto.images
                print("habilitado inicial", habilitado)
                if habilitado:
                    habilitado=True
                else:
                    habilitado=False


                print("habilitado final", habilitado)
                if producto:
                    print("POST --> UPDATE")
                    # UPDATE 
                    producto = Product(
                        id=product_id ,
                        product_name=product_name,
                        slug=slugify(product_name).lower(),
                        description=description,
                        price=price,
                        images=images,
                        stock=stock,
                        is_available=habilitado,
                        category=category,
                        created_date =created_date, 
                        modified_date=datetime.today(),
                    )
                    producto.save()
                else:
                    print("Producto no encontrado")
            else:
                # ADD
                print("POS --> ADD")
                print(slugify(product_name))

                producto = Product(
                        product_name=product_name,
                        slug=slugify(product_name).lower(),
                        description= description,
                        price=price,
                        images=images,
                        stock=stock,
                        is_available=True,
                        category=category,
                        created_date= datetime.today(),
                        modified_date=datetime.today(),
                        )
                if producto:
                    producto.save()
                    product_id = producto.id

            return redirect('panel_catalogo')
    
    return redirect('panel') 

def panel_producto_img(request):

    
    try:
        
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user.id, codigo__codigo ='PRODUCTO')  
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)     
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Validar Acceso
    
    if accesousuario.codigo.codigo =='PRODUCTO':
          
        if request.method =="POST":
            product_id = request.POST.get("product_id")

            try:
                if request.FILES["imgFile"]:
                    fileitem = request.FILES["imgFile"]
                    
                imgroot = "photos/products/none.jpg" #default
                # check if the file has been uploaded
                if fileitem.name:
                    # strip the leading path from the file name
                    fn = os.path.basename(fileitem.name)
                    # open read and write the file into the server
                    open(f"media/photos/products/{fn}", 'wb').write( fileitem.file.read())  #"/media/photos/products/
                    
                    imgroot = f"photos/products/{fileitem}"

                if product_id:
                    producto = Product.objects.filter(id=product_id).first()
                    #UPDATE IMAGE
                    print("***  UPDATE IMAGE ***")
                    producto = Product(
                            id=product_id ,
                            images=imgroot,
                            product_name=producto.product_name,
                            slug=slugify(producto.product_name).lower(),
                            description=producto.description,
                            price=producto.price,
                            stock=producto.stock,
                            is_available=True,
                            category=producto.category,
                            created_date =producto.created_date, 
                            modified_date=datetime.today(),
                            )
                    producto.save()
                    return redirect('panel_producto_detalle', str(product_id))
            except:
                print("No selecciono imagen")
                return redirect('panel_producto_detalle', str(product_id))
        return redirect('panel')
    return redirect('panel') 

def panel_producto_habilitar(request,product_id=None,estado=None):

    try:
        
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user.id, codigo__codigo ='PRODUCTO')  
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)     
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Validar Acceso
    
    if accesousuario.codigo.codigo =='PRODUCTO':
          
            print(product_id,"product ID")
            habilitado = estado
            try:
                print("habilitado inicial", habilitado)
                if habilitado==1:
                    habilitado=True
                else:
                    habilitado=False

                if product_id:
                    producto = Product.objects.filter(id=product_id).first()
                    #UPDATE SATUS
                    print("***  UPDATE STATUS ***")
                    producto = Product(
                            id=product_id,
                            is_available=habilitado,
                            images=producto.images,
                            modified_date=datetime.today(),
                            product_name=producto.product_name,
                            slug=slugify(producto.product_name).lower(),
                            description=producto.description,
                            price=producto.price,
                            stock=producto.stock,
                            category=producto.category,
                            created_date =producto.created_date, 
                            )
                    producto.save()

                    return redirect('panel_catalogo')
            except:
                print("Error: ", producto.product_name)        
            
    return redirect('panel_catalogo')

def panel_usuario_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PERMISOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PERMISOS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        usuarios = Account.objects.filter(is_staff=True)
        cantidad = usuarios.count()

        context = {
            'usuarios':usuarios,
            'permisousuario':permisousuario,
            'cantidad':cantidad,
        }
        print(usuarios)
        return render(request,'panel/lista_usuarios.html',context) 

    return render(request,'panel/login.html',)

def panel_usuario_permisos(request,user_id=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PERMISOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PERMISOS':
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        usuario = Account.objects.filter(id=user_id)
        cantidad = usuario.count()
        permisos = Permition.objects.filter().all()



    
        context = {
            'permisos':permisos,
            'usuario':usuario,
            'permisousuario':permisousuario,
            'cantidad':cantidad,
            }
     
        return render(request,'panel/usuario_permisos.html',context) 

    return render(request,'panel/login.html',)

def panel_edit_profile(request):

    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Su perfil ha sido actualizado.')
            return redirect('panel')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'panel/usuario_panel_perfil.html', context)

def panel_usuario_permisos_reasignar(request,user_id=None):
    #Carga los permisos no asignados al usuario para poder editarlos.
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PERMISOS')
            if accesousuario:
                if accesousuario.modo_editar==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PERMISOS':
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        permisos_usr = AccountPermition.objects.filter(user=user_id) #Todo lo asignado

        permisos = Permition.objects.filter(~Q(codigo__in=[o.codigo for o in permisos_usr])) #Todos los permisos que no tiene asignado el usuario

       
        usuario = Account.objects.get(id=user_id)
         

        context = {
            'permisos':permisos, # PERMISOS NO ASIGNADOS //Todos los permisos que no tiene asignado el usuario
            'usuario':usuario, #Datos del usuario
            'permisousuario':permisousuario, # Permisos del usuario logueado
            'permisos_usr':permisos_usr,     #PERMISOS ASIGNADOS // Permisos del usuario Consultado
            }
        
        return render(request,'panel/usuario_permisos.html',context) 

    return render(request,'panel/login.html',)

def panel_usuario_permisos_actualizar(request,user_id=None,id_pk=None,codigo=None,tipo=None,valor=None):  #Tipo (Ver (1) / Modificar(2)) - Valor (True / False)
    #Carga los permisos no asignados al usuario para poder editarlos.
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PERMISOS')
            if accesousuario:
                if accesousuario.modo_editar==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PERMISOS':
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')


        usuario = Account.objects.get(id=user_id)
        permisos_usr = AccountPermition.objects.filter(id=id_pk).first()
        permiso =  Permition.objects.filter(pk=codigo).first()
        if permiso:
            if permisos_usr:
                if tipo==1 and valor==1: #Ver=True 
                    print("Actualizo  Ver=True")
                    
                    permisos_usr = AccountPermition(
                        id=id_pk,
                        codigo=permiso,
                        modo_ver=valor,
                        user = usuario,    
                        )
                    permisos_usr.save()

                if tipo==1 and valor==0: #Ver=False / Edit = False 
                    print("Actualizo  Ver=False")
                    
                    permisos_usr = AccountPermition(
                        id=id_pk,
                        codigo=permiso,
                        modo_ver=False,
                        modo_editar=False,
                        user = usuario,    
                        )
                    permisos_usr.save()

                if tipo==2 and valor==1: #Edit = True
                    print("Actualizo  Editar=True")
                    permisos_usr = AccountPermition(
                        id=id_pk,
                        codigo=permiso,
                        modo_ver=True,
                        modo_editar=True,
                        user = usuario,    
                        )
                    permisos_usr.save()

                if tipo==2 and valor==0: #Edit = False
                    print("Actualizo  Editar=False")
                    permisos_usr = AccountPermition(
                        id=id_pk,
                        codigo=permiso,
                        modo_editar=False,
                        modo_ver=permisos_usr.modo_ver,
                        user = usuario,    
                        )
                    permisos_usr.save()


            else:
                print("Agregar nuevo para ver")
                if tipo==1 and valor==1: #VER=True
                    permisos_usr = AccountPermition(
                        user=usuario,
                        codigo=permiso ,
                        modo_ver=True,  
                        modo_editar=False
                            )
                    permisos_usr.save()

                if tipo==1 and valor==0: #VER=False
                    permisos_usr = AccountPermition(
                        user=usuario,
                        codigo=permiso,
                        modo_ver=False,  
                        modo_editar=False
                            )
                    permisos_usr.save()

                if tipo==2 and valor==1: #Editar=True
                    
                    permisos_usr = AccountPermition(
                        user=usuario,
                        codigo=permiso ,
                        modo_ver=True,  
                        modo_editar=True
                            )
                    permisos_usr.save()
                if tipo==2 and valor==0: #Editar=True
                    
                    permisos_usr = AccountPermition(
                        user=usuario,
                        codigo=permiso ,
                        modo_editar=False,
                            )
                    permisos_usr.save()
        else:
            print("No se encontró el permiso")
        
        permisos_usr = AccountPermition.objects.filter(user=user_id,codigo=codigo)
        permisos = Permition.objects.exclude(pk__in=permisos_usr)

        context = {
            'permisos':permisos, # PERMISOS NO ASIGNADOS //Todos los permisos que no tiene asignado el usuario
            'usuario':usuario, #Datos del usuario
            'permisousuario':permisousuario, # Permisos del usuario logueado
            'permisos_usr':permisos_usr,     #PERMISOS ASIGNADOS // Permisos del usuario Consultado
            }
        
        
        return redirect('panel_usuarios_reasignar',user_id) 
       

    return render(request,'panel/login.html',)

def panel_cliente_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CLIENTE')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CLIENTE':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        usuarios = Account.objects.filter(is_staff=False)
        cantidad = usuarios.count()

        context = {
            'usuarios':usuarios,
            'permisousuario':permisousuario,
            'cantidad':cantidad,
        }
        print(usuarios)
        return render(request,'panel/lista_clientes.html',context) 

    return render(request,'panel/login.html',)

def panel_cliente_detalle(request,id_cliente=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CLIENTE')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CLIENTE':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        usuarios = Account.objects.filter(id=id_cliente).first()
        pedidos = Order.objects.filter(email=usuarios.email)
        compras = pedidos.count()


        context = {
            'usuarios':usuarios,
            'permisousuario':permisousuario,
            'compras':compras,
        }
        print(usuarios.email,compras)
        return render(request,'panel/cliente_detalle.html',context) 

    return render(request,'panel/login.html',)

def panel_registrar_pago(request,order_number=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PEDIDOS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if order_number:
            orden = Order.objects.get(order_number=order_number)
            cuentas = Cuentas.objects.all()
            total = orden.order_total + orden.envio
        context = {
            'orden':orden,
            'cuentas':cuentas,
            'permisousuario':permisousuario,
            'total':total,
        
        }
        print(orden)
        return render(request,'panel/registrar_pago.html',context) 

    return render(request,'panel/login.html',)
    
def panel_confirmar_pago(request,order_number=None):

    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
    print("confirmar pago efectivo / transferencia")
    if accesousuario.codigo.codigo =='PEDIDOS':
       
        if request.method =="POST":
            # GRABAR TRX EN PAYMENT
            total = 0  #Subtotal items + costo envio
            subtotal=0  #Subtotal 
            envio=0
            quantity=0
            current_user = request.user

           
            envio = request.POST.get("envio")
            cuenta_id = request.POST.get("cuenta")

             # If the cart count is less than or equal to 0, then redirect back to shop
            order = Order.objects.get(order_number=order_number, is_ordered=True)
            ordered_products = OrderProduct.objects.filter(order_id=order.id)

            order_count_items = ordered_products.count()

            if order_count_items <= 0:
                return redirect('store')

            for cart_item in ordered_products:
                #subtotal += (cart_item.product.price * cart_item.quantity) No se toma precio de lista
                subtotal += (cart_item.product_price * cart_item.quantity)  #Precio ya cerrado
                #subtotal += cart_item.product_price
                quantity += cart_item.quantity

            total =  float(envio) + float(subtotal)
            print(total,quantity,subtotal)
            #GRABO TRANSACCION DE PAGO
            if order:
                payment = Payment(
                    user = current_user,
                    payment_id = "Pago Manual",
                    payment_method = "Efectivo / Transf",
                    amount_paid = total,
                   
                    status = "Cobrado",
                )
                payment.save()
                payment_id = payment.id

                # CAMBIAR ESTADO PEDIDO
                order.payment = payment
                order.is_ordered = True
                order.status = "Cobrado"
                order.envio = envio
                order.order_total=total
                order.save()
                
               # GRABAR TRX EN MOVIMIENTOS
                current_date = datetime.today()
                oper = Operaciones.objects.filter(codigo="ING").first() #Ingresos
                cuentas= Cuentas.objects.get(id=cuenta_id)
            

                cliente = order.last_name + ", " + order.first_name
                trx = Movimientos(
                        fecha =current_date,
                        cliente = cliente,
                        movimiento = oper,
                        cuenta = cuentas,
                        monto=total,
                        observaciones = "Cobro Trx: " + order.order_number,
                        idtransferencia = 0,
                        ordernumber = order, #Nro de orden
                )
                trx.save()
                
                return redirect('panel_pedidos','New') 

    return render(request,'panel/login.html',)

def panel_movimientos_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='MOVIMIENTOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='MOVIMIENTOS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        mov = Movimientos.objects.filter()
        cuentas = Cuentas.objects.all()
        
        context = {
            'mov':mov,
            'permisousuario':permisousuario,
            'cuentas':cuentas,
                       
        }
        
        return render(request,'panel/lista_movimientos.html',context) 

    return render(request,'panel/login.html',)

def panel_transferencias_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='TRANSFERENCIAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='TRANSFERENCIAS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        transf = Transferencias.objects.filter()
        cuentas = Cuentas.objects.all()
        
        context = {
            'transf':transf,
            'permisousuario':permisousuario,
            'cuentas':cuentas,
                       
        }
        
        return render(request,'panel/lista_transferencias.html',context) 

    return render(request,'panel/login.html',)

def panel_importar_productos(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='IMPORTAR PRODUCTOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='IMPORTAR PRODUCTOS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
        context = {
            'permisousuario':permisousuario,
            'modelo':2,
                       
        }
        
        return render(request,'panel/importar_productos.html',context) 

    return render(request,'panel/login.html',)
    
def export_xls(request,modelo=None):

    #MODELO:
    #1 - Movimientos 
    #2 - Pedidos
    #3 - Productos

    print("Export to Excel")
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition']='attachment; filename=movimiento'+ str(datetime.now()) + '.xls'
    wb = xlwt.Workbook(encoding='utf-8')


    if modelo==1: #MOVIMIENTOS

        #Para cada Caja genero una pagina
        cuentas = Cuentas.objects.all()

        if cuentas:
            for i in cuentas:
                sheet = str(i)
                ws = wb.add_sheet(sheet)
                
                row_num=0
                font_style= xlwt.Style.XFStyle()
                font_style.font.bold = True
                columns = ['fecha','cliente','movimiento','monto','observaciones','idtransferencia','ordernumber']
                for col_num in range(len(columns)):
                    ws.write(row_num,col_num,columns[col_num],font_style)
                font_style = xlwt.Style.XFStyle()
                rows = Movimientos.objects.filter(cuenta=i).all().values_list(
                    'fecha','cliente','movimiento','monto','observaciones','idtransferencia','ordernumber')
                for row in rows:
                    row_num += 1
                    for col_num in range(len(row)):
                        if col_num==3:
                            monto = float("{0:.2f}".format((float)(row[3])))
                            #ws.write(row_num,col_num,'$ '+str('{0:,}'.format(int(round(monto)))))
                            ws.write(row_num,col_num,int(round(monto)))
                        else:
                            ws.write(row_num,col_num, str(row[col_num]),font_style)
            wb.save(response)
    if modelo==2: #PEDIDOS
        count_status=3
        
        for i in range(count_status):
           
            if i  == 0:
                sheet = "New"
                ws = wb.add_sheet(sheet)
            elif i == 1 :
                sheet = "Cobrado"
                ws = wb.add_sheet(sheet)
            elif i == 2 :
                sheet = "Entregado"
                ws = wb.add_sheet(sheet)
        
            row_num=0
            font_style= xlwt.Style.XFStyle()
            font_style.font.bold = True
            columns = ['user','payment','order_number','first_name','last_name','email','dir_telefono','dir_calle','dir_nro',
                        'dir_localidad','dir_provincia','dir_cp','dir_obs','dir_correo','order_note','order_total','envio','status',
                        'ip','is_ordered','created_at','updated_at']
            for col_num in range(len(columns)):
                ws.write(row_num,col_num,columns[col_num],font_style)
            font_style = xlwt.Style.XFStyle()

            rows = Order.objects.filter(status=sheet).all().values_list(
                'user','payment','order_number','first_name','last_name','email','dir_telefono','dir_calle','dir_nro',
                'dir_localidad','dir_provincia','dir_cp','dir_obs','dir_correo','order_note','order_total','envio','status',
                'ip','is_ordered','created_at','updated_at').order_by('-created_at')
            for row in rows:
                row_num += 1
                for col_num in range(len(row)):
                    if col_num==15 or col_num==16:
                        monto = float("{0:.2f}".format((float)(row[col_num])))
                        ws.write(row_num,col_num,int(round(monto)))
                    else:
                        ws.write(row_num,col_num, str(row[col_num]),font_style)
        wb.save(response)


    return response

def import_productos_xls(request):

    cant_ok = 0
    cant_error =0
    error_str=""
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    articulos_tmp = ImportTempProduct.objects.filter(usuario=request.user)

    #FORMATO PARA IMPORTAR PRODUCTOS
    #product_name,description,variation_category,variation_value,price,images,stock,habilitado,category
    #response = HttpResponse(content_type='application/ms-excel')
    #Copio el archivo localmente
    if request.method=="POST":
        try:
            myfile = request.FILES['rootfile']
            if myfile:
                fs = FileSystemStorage()
                filename = fs.save(myfile.name,myfile)
                archivo = fs.url(filename)
        
                int_fin = len(archivo)
                archivo = archivo[1:int_fin]
        except:
            archivo=""

        #archivo="media/FULL_LIFCHE.xls"
        if archivo:
        
            print("*********--->", archivo, "<------******************")
            workbook = xlrd.open_workbook(archivo)
            
            #Get the first sheet in the workbook by index
            sheet1 = workbook.sheet_by_index(0)

            #Borro todo lo anterior
            tmp_producto = ImportTempProduct.objects.filter(usuario = request.user)
            if tmp_producto:
                tmp_producto.delete()

            #Get each row in the sheet as a list and print the list
            for rowNumber in range(sheet1.nrows):
                try:
                    row = sheet1.row_values(rowNumber)
                    if sheet1.cell_value(rowNumber, 0) != "product_name":
                        product_id=0
                        product_name = sheet1.cell_value(rowNumber, 0)
                        tmp_producto = ImportTempProduct.objects.filter(product_name=product_name, usuario = request.user).first()
                        if not tmp_producto:
                            #Valido que exista la categoria
                            cat_name = sheet1.cell_value(rowNumber, 8).lower()

                            cat = Category.objects.get(category_name__icontains=cat_name)
                            if cat:
                                tmp_producto = ImportTempProduct(
                                    product_name=product_name,
                                    slug=slugify(product_name).lower(),
                                    description= sheet1.cell_value(rowNumber, 1),
                                    variation_category = sheet1.cell_value(rowNumber, 2),
                                    variation_value = sheet1.cell_value(rowNumber, 3),
                                    price=sheet1.cell_value(rowNumber, 4),
                                    images=sheet1.cell_value(rowNumber, 5),
                                    stock=sheet1.cell_value(rowNumber, 6),
                                    is_available=sheet1.cell_value(rowNumber, 7),
                                    category=cat.category_name, #  sheet1.cell_value(rowNumber, 8),
                                    created_date= datetime.today(),
                                    modified_date=datetime.today(),
                                    usuario = request.user,
                                        )
                                tmp_producto.save()
                                if tmp_producto:
                                    product_id = tmp_producto.id
                                    cant_ok=cant_ok+1
                                else:
                                    cant_error=cant_error+1
                                    error_str = error_str + "Error al grabar el registro ROW: " + str(rowNumber)
                            else:
                                error_str = error_str + "Categoría inexistente " + cat_name + " ROW: " + str(rowNumber)
                                cant_error=cant_error+1

                    #print("OK",cant_ok,"Error",cant_error)
                    
                except OSError as err:
                    print("OS error:", err)
                    error_str = error_str + err + " ROW: " + str(rowNumber)
                    cant_error=cant_error+1
                    pass
                except ValueError:
                    cant_error=cant_error+1
                    error_str = error_str  + " Error al convertir int -  ROW: " + str(rowNumber)  
                    print("Could not convert data to an integer.")
                    pass
                except Exception as err:
                    error_str= error_str + product_name
                    error_str= error_str + f"Unexpected {err=}, {type(err)=}"
                    cant_error=cant_error+1
                    pass
                    #raise:
                    #print("Salio por Exception")
                    #print("Linea", rowNumber, "Producto", product_name, KeyError())
                    #return render (request,'panel/importar.html',{'error':'No se pudo cargar el archivo'})

            #Borro el archivo
            os.remove(archivo)
            
    context = {
                'cant_ok':cant_ok,
                'permisousuario':permisousuario,
                'cant_error':cant_error,
                'error_str':error_str,
                'articulos_tmp':articulos_tmp,
                        
                }
    return render(request,'panel/importar_productos.html',context)

def guardar_tmp_productos(request): 
   
    articulos_tmp = ImportTempProduct.objects.filter(usuario=request.user)

    if articulos_tmp:
        for a in articulos_tmp:
            try:
                producto = Product.objects.filter(product_name=a.product_name)
                
                if not producto:
                    if not a.images:
                      imagen = "photos/products/none.jpg" #default      
                    else:
                        imagen = a.images

                    producto = Product(
                        product_name = a.product_name,
                        slug=slugify(a.product_name).lower(),
                        description = a.description,
                        category = Category.objects.get(category_name=a.category),
                        images = imagen,
                        stock = a.stock,
                        price = float(a.price),
                        is_available = a.is_available,
                        created_date= datetime.today(),
                        modified_date=datetime.today(),
                    )
                    producto.save()
            except ObjectDoesNotExist:
                print ("articulo ya existente ", a.product_name )

            except Exception as err:
                print(a.product_name, f"Unexpected {err=}, {type(err)=}")


    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    catalogo = Product.objects.filter().all()
    cantidad = catalogo.count()

    context = {
        'catalogo':catalogo,
        'permisousuario':permisousuario,
        'cantidad':cantidad
        }
    return render(request,'panel/lista_productos.html',context)

def panel_importar_productos_del(request,product_id=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='IMPORTAR PRODUCTOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

    if accesousuario.codigo.codigo =='IMPORTAR PRODUCTOS':

       
        
        if product_id:
            producto = ImportTempProduct.objects.filter(id=product_id,usuario= request.user)
            if producto:
                producto.delete()


        articulos_tmp = ImportTempProduct.objects.filter(usuario=request.user)
       
        context = {
                'cant_ok':'',
                'permisousuario':permisousuario,
                'cant_error':'',
                'error_str':'',
                'articulos_tmp':articulos_tmp,
                        
                }
        return render(request,'panel/importar_productos.html',context)


    return render(request,'panel/login.html',)             

def panel_categoria_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CATEGORIA')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CATEGORIA':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        categoria = Category.objects.filter().all()
        context = {
            'categoria':categoria,
            'permisousuario':permisousuario,
           
        }
       
        return render(request,'panel/lista_categorias.html',context) 

    return render(request,'panel/login.html',)

def panel_categoria_del(request,id_categoria=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CATEGORIA')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CATEGORIA':


        if id_categoria:
            categoria = Category.objects.filter(id=id_categoria)
            if categoria:
                categoria.delete()


        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categoria = Category.objects.filter().all()

        context = {
            'categoria':categoria,
            'permisousuario':permisousuario,
           
        }
       
        return render(request,'panel/lista_categorias.html',context) 

    return render(request,'panel/login.html',)

def panel_categoria_detalle(request,categoria_id=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CATEGORIA')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CATEGORIA':

        if request.method =="GET":

            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            if categoria_id:
                categoria = Category.objects.get(id=categoria_id)
            else:
                categoria=[]

            context = {
                'categoria':categoria,
                'permisousuario':permisousuario,
           
                }
       
            return render(request,'panel/categoria_detalle.html',context) 

        if request.method =="POST":
            cat_id = request.POST.get("categoria_id")
            cat_nombre = request.POST.get("category_name")
            cat_descripcion = request.POST.get("description")
            cat_imagen = request.POST.get("images")
            

            # *** IMAGEN *****
            try:
                if request.FILES["imgFile"]:
                    print("Cambio de imagen")
                    fileitem = request.FILES["imgFile"]
                    # check if the file has been uploaded
                    if fileitem.name:
                        # strip the leading path from the file name
                        fn = os.path.basename(fileitem.name)
                        # open read and write the file into the server
                        open(f"media/photos/categories/{fn}", 'wb').write( fileitem.file.read())  #"/media/photos/products/
                        cat_imagen = f"photos/categories/{fileitem}"
                        #cat_imagen = f"{fileitem}"
                        
            except:
                if cat_id:
                    categoria = Category.objects.get(pk=cat_id)
                    if categoria:
                        if not categoria.cat_image:
                            cat_imagen = "photos/categories/none.jpg" #default
                        else:
                            cat_imagen = categoria.cat_image
                else: #Categoria Nueva
                    if not cat_imagen:
                        cat_imagen = "photos/categories/none.jpg" #default    

            if cat_id:
                categoria = Category.objects.get(pk=cat_id)  
                if categoria:
                    category = Category(
                        id=cat_id,
                        category_name=cat_nombre ,
                        slug = slugify(cat_nombre),
                        description = cat_descripcion,
                        cat_image = cat_imagen,
                    )
                    category.save()
            else:
                category = Category(
                    category_name=cat_nombre ,
                    slug = slugify(cat_nombre),
                    description = cat_descripcion,
                    cat_image = cat_imagen,
                )
                category.save()
            categoria = Category.objects.filter().all()         
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
            context = {
                'categoria':categoria,
                'permisousuario':permisousuario,
            
            }
        
            return render(request,'panel/lista_categorias.html',context) 

    return render(request,'panel/login.html',)

def import_pedidos_xls(request):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='IMPORTAR PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    #Borro todo lo anterior Encabezado
    pedidos_tmp = ImportTempOrders.objects.filter(usuario = request.user)
    if pedidos_tmp:
        pedidos_tmp.delete()


    #Borro todo lo anterior Detalle
    articulos_tmp = ImportTempOrdersDetail.objects.filter(usuario = request.user)
    if articulos_tmp:
        articulos_tmp.delete()
    
    cant_ok=0
    cant_error=0
    error_str = ""
    articulos_tmp = []
    pedidos_tmp=[]
   
    if accesousuario.codigo.codigo =='IMPORTAR PEDIDOS':

        #Leer archivo
        archivo=""
        if request.method=="POST":
            try:
                myfile = request.FILES['rootfile']
                if myfile:
                    fs = FileSystemStorage()
                    filename = fs.save(myfile.name,myfile)
                    archivo = fs.url(filename)
            
                    int_fin = len(archivo)
                    archivo = archivo[1:int_fin]
            except:
                archivo=""

        #archivo="media/Pedidos.xls"
    
        if archivo:
        
            print("*********--->", archivo, "<------******************")
            workbook = xlrd.open_workbook(archivo)
             #Get the first sheet in the workbook by index
            sheet1 = workbook.sheet_by_index(0)
            
            
            #Borro todo lo anterior Encabezado
            pedidos_tmp = ImportTempOrders.objects.filter(usuario = request.user)
            if pedidos_tmp:
                pedidos_tmp.delete()

           
            #Borro todo lo anterior Detalle
            articulos_tmp = ImportTempOrdersDetail.objects.filter(usuario = request.user)
            if articulos_tmp:
                articulos_tmp.delete()
            
           
            #Get each row in the sheet as a list and print the list
            for rowNumber in range(sheet1.nrows):
                try:
                    if sheet1.cell_value(rowNumber, 0) != "Codigo":  #Paso el encabezado
                        codigo = sheet1.cell_value(rowNumber, 0)
                        #print("Linea ",rowNumber," codigo: ",codigo)
                        
                        pedidos_tmp = ImportTempOrders.objects.filter(codigo=codigo, usuario = request.user).first()
                        if not pedidos_tmp:
                            try:
                                str_field       = "correo"
                                correo =    str(sheet1.cell_value(rowNumber, 6))  #Entrega en correo
                                if correo[0:2].lower().strip() =="si":
                                    print("Correo Argentino SI", correo[0:2].lower().strip() )
                                    bcorreo = True
                                else:
                                    print("Correo Argentino NO", correo[0:2].lower().strip() )
                                    bcorreo = False

                                nombre_completo= str(sheet1.cell_value(rowNumber, 5))
                                i_end = nombre_completo.find(" ")
                                nombre = nombre_completo[0:i_end]
                                apellido = nombre_completo[i_end:len(nombre_completo)]
                                #Tomo los datos de la linea
                                str_field   = "first_name"
                                first_name  = nombre
                                str_field   = "Nombre"
                                last_name   = apellido
                                str_field   = "email"
                                email               = str(sheet1.cell_value(rowNumber, 7)) #email
                                str_field   = "date"
                                created_date        =  sheet1.cell_value(rowNumber, 1) #fecha
                                modified_date       =  sheet1.cell_value(rowNumber, 1) #fecha
                                str_field  = "Order Total"
                                order_total         = sheet1.cell_value(rowNumber, 2) #Order Total
                                str_field  = "Telefono"
                                dir_telefono        =  str(sheet1.cell_value(rowNumber, 12)) #Telefono
                                str_field  = "Calle"
                                dir_calle           =  str(sheet1.cell_value(rowNumber, 8)) #Calle
                                dir_nro             = "0"
                                str_field  = "Localidad"
                                dir_localidad       = sheet1.cell_value(rowNumber, 9) #Localidad
                                str_field  = "Provincia"
                                dir_provincia       = sheet1.cell_value(rowNumber, 11) #Provincia
                                str_field  = "CP"
                                dir_cp              = sheet1.cell_value(rowNumber, 10) #CP
                                str_field  = "Obs"
                                dir_obs             = sheet1.cell_value(rowNumber, 13) #Observaciones
                                usuario             = request.user
                                #LISTADO DE ARTICULOS
                                mensaje = sheet1.cell_value(rowNumber, 4)
                                #print(correo,first_name,email)
                                #print(dir_telefono,dir_calle,dir_calle,dir_nro,dir_localidad,dir_obs)
                                
                                new_pedido = ImportTempOrders.objects.filter(codigo=codigo)
                                if not new_pedido:
                                    new_pedido=ImportTempOrders(
                                        codigo          = codigo,
                                        first_name      = first_name ,
                                        last_name       = last_name   ,
                                        email           = email     ,
                                        created_at      = created_date,
                                        updated_at      = modified_date,
                                        order_total     = order_total,
                                        dir_telefono    = dir_telefono,
                                        dir_calle       = dir_calle,
                                        dir_nro         = dir_nro,
                                        dir_localidad   = dir_localidad,
                                        dir_provincia   = dir_provincia,
                                        dir_cp          = dir_cp,
                                        dir_obs         = dir_obs,
                                        dir_correo      = bcorreo,
                                        usuario        = request.user
                                        )                                    
                                    new_pedido.save()
                                
                                    if new_pedido:       
                                        #LINEAS DE ARTICULOS                                
                                        if "?pedido=" in mensaje:
                                            i_start_ped = mensaje.find('?pedido=')
                                            i_end_ped = mensaje.find('*',i_start_ped)
                                            codigo_ped = mensaje[i_start_ped + 8 :i_end_ped]
                                            print("Codigo Detalle",codigo_ped,codigo)
                                       
                                        if codigo == codigo_ped:
                                            #Recorro artiuclos
                                            if "*Pedido:*" in mensaje:
                                                i_start_ped = mensaje.find('*Pedido:*')
                                                i_start_ped = i_start_ped   #Arranca linea 
                                                mensaje = mensaje[i_start_ped+9:len(mensaje)]
                                                i_start_ped = mensaje.find('* x *') -4
                                                #print("INICIO",mensaje)
                                                i=1
                                                i_fin_linea=0
                                                total_items=0
                                               
                                            while i_end_ped > 0:
                                               
                                                i_end_ped = mensaje.find('Subtotal',i_start_ped)
                                                i_end_ped = mensaje.find('*',i_end_ped) # proxima cantidad
                                                linea = mensaje[i_start_ped:i_end_ped]
                                                if i_end_ped >= 1:
                                                    if linea.find('_Cant. Artículos') > 0:
                                                        i_fin_linea = linea.find('_Cant. Artículos')
                                                        linea = mensaje[i_start_ped:i_fin_linea]
                                                        
                                                    #*5* x *Letra 12 mm - A - SILICONA*   - |  Subtotal = $1125
                                                    #Tomo los datos de la linea
                                                    # ** CANTIDAD  **
                                                    
                                                    i_ini_linea = linea.find('*')+1
                                                    i_fin_linea = linea.find('*',i_ini_linea)
                                                    quantity = linea[i_ini_linea:i_fin_linea]
                                                    #print("quantity:",quantity)
                                                    linea = linea[i_fin_linea+1:len(linea)]
                                                    # ** PRODUCTO **
                                                    i_ini_linea = linea.find('*')+1
                                                    i_fin_linea = linea.find('*',i_ini_linea)
                                                    product = linea[i_ini_linea:i_fin_linea]  #.strip().replace('\r','').replace('\n')
                                                    #print("Producto ", product)
                                                    linea = linea[i_fin_linea+1:len(linea)]
                                                    # ** SUBTOTAL **
                                                    i_ini_linea = linea.find('$')+1
                                                    #print("linea",linea[i_ini_linea:len(linea)])
                                                    subtotal = float(linea[i_ini_linea:len(linea)])
                                                    #print("subtotal ", str(subtotal))
                                                    if subtotal>0:
                                                        total_items = total_items + subtotal
                                                    #print("Total Items",str(total_items))
                                                    
                                                    try:
                                                        codigo = codigo
                                                    
                                                        new_linea_pedido = ImportTempOrdersDetail(
                                                            codigo = codigo,
                                                            product = product,
                                                            quantity = quantity,
                                                            subtotal = subtotal,
                                                            usuario = usuario,
                                                            status = False
                                                            )
                                                        new_linea_pedido.save()
                                                    except Exception as err:
                                                        error_str= error_str + 'Artículo: ' + product + 'Linea: ' + str(i)
                                                        error_str= error_str + f"Unexpected {err=}, {type(err)=}"
                                                else:
                                                    #ultima linea
                                                    i_end_ped = mensaje.find('_Cant. Artículos',i_end_ped) # Ultima linea
                                                    linea = mensaje[i_start_ped:i_end_ped]
                                                    
                                                mensaje = mensaje[i_end_ped:len(mensaje)]
                                                i=i+1



                            except Exception as err:
                                error_str= error_str + codigo + "linea:" + str(rowNumber) + " campo: " + str_field
                                error_str= error_str + f"Unexpected {err=}, {type(err)=}"
                                cant_error=cant_error+1
                                pass
                    
                except OSError as err:
                    print("OS error:", err)
                    error_str = error_str + err + " ROW: " + str(rowNumber)
                    cant_error=cant_error+1
                    pass
                except ValueError:
                    cant_error=cant_error+1
                    error_str = error_str  + " Error al convertir int -  ROW: " + str(rowNumber)  
                    print("Could not convert data to an integer.")
                    pass
                except Exception as err:
                    error_str= error_str + codigo
                    error_str= error_str + f"Unexpected {err=}, {type(err)=}"
                    cant_error=cant_error+1
                    pass
                    #raise:
                    #print("Salio por Exception")
                    #print("Linea", rowNumber, "Producto", product_name, KeyError())
                    #return render (request,'panel/importar.html',{'error':'No se pudo cargar el archivo'})

            #Borro el archivo
            os.remove(archivo) 
            #print("Ejecutar validacion de articulos")
            validar_tmp_pedidos(request)   
    
    pedidos_tmp = ImportTempOrders.objects.filter(usuario = request.user).order_by('codigo')
    articulos_tmp = ImportTempOrdersDetail.objects.filter(usuario = request.user).order_by('codigo')
    cant_ok = pedidos_tmp.count()
    
    context = {
                'cant_ok':cant_ok,
                'permisousuario':permisousuario,
                'cant_error':cant_error,
                'error_str':error_str,
                'pedidos_tmp':pedidos_tmp,
                'articulos_tmp':articulos_tmp,
                                        
                }
    return render(request,'panel/importar_pedidos.html',context)

def validar_tmp_pedidos(request):
    
    #print("validar_tmp_pedidos")

    pedidos_tmp = ImportTempOrders.objects.filter(usuario=request.user)
    if pedidos_tmp:
        
        for enc in pedidos_tmp:
            order_total = 0
            print("Temp pedidos Create", enc.updated_at)
            pedidos_det_tmp = ImportTempOrdersDetail.objects.filter(usuario=request.user,codigo=enc.codigo)
            if pedidos_det_tmp:
                for a in pedidos_det_tmp:
                    try:
                        producto = Product.objects.filter(product_name__icontains  =a.product).first()
                        if producto:
                            product_name = producto.product_name
                            detalle_pedido = ImportTempOrdersDetail(
                                id=a.id,
                                codigo = a.codigo,
                                status=True,
                                quantity=a.quantity,
                                subtotal=a.subtotal,
                                product = product_name,
                                usuario = a.usuario
                                )
                            order_total = order_total + a.subtotal
                            detalle_pedido.save()
                  

                    except Exception as err:
                        #print("Error no controlado: ", a.product)
                        #print(f"Unexpected {err=}, {type(err)=}")
                        pass
            encabezado = ImportTempOrders(
                id=enc.id,
                codigo=enc.codigo,
                first_name=enc.first_name,
                last_name=enc.last_name,
                email=enc.email,
                created_at=enc.created_at,
                updated_at=enc.updated_at,
                usuario=enc.usuario,
                dir_telefono=enc.dir_telefono,
                dir_calle=enc.dir_calle,
                dir_nro =enc.dir_nro,
                dir_localidad=enc.dir_localidad,
                dir_provincia=enc.dir_provincia,
                dir_cp = enc.dir_cp,
                dir_obs = enc.dir_obs,
                dir_correo= enc.dir_correo,
                order_total = order_total 
            ) 
            print("encabezado updated_at:", encabezado.updated_at)
            encabezado.save()
                          
def guardar_tmp_pedidos(request,codigo=None):
    
    if codigo:
        #Importar 1
        #print("Guardar pedido: ",codigo)
        pedidos_tmp = ImportTempOrders.objects.filter(usuario=request.user,codigo=codigo).first()
        if pedidos_tmp:
            id_pedido=pedidos_tmp.id
            order = Order.objects.filter(order_number=codigo)
            if not order:
                #print("El pedido no existe, lo grabo")
                user_account = Account.objects.get(email=request.user)
                if user_account:
                    
                    Order_New = Order(
                        order_number=codigo,
                        first_name=pedidos_tmp.first_name,
                        last_name=pedidos_tmp.last_name,
                        email=pedidos_tmp.email,
                        created_at=pedidos_tmp.created_at,
                        fecha=pedidos_tmp.created_at,
                        updated_at=pedidos_tmp.updated_at,
                        user=user_account,
                        dir_telefono=pedidos_tmp.dir_telefono,
                        dir_calle=pedidos_tmp.dir_calle,
                        dir_nro =pedidos_tmp.dir_nro,
                        dir_localidad=pedidos_tmp.dir_localidad,
                        dir_provincia=pedidos_tmp.dir_provincia,
                        dir_cp = pedidos_tmp.dir_cp,
                        dir_obs = pedidos_tmp.dir_obs,
                        dir_correo= pedidos_tmp.dir_correo,
                        order_total = pedidos_tmp.order_total,
                        envio = 0,
                        status = "New",
                        is_ordered=True,
                        ip = request.META.get('REMOTE_ADDR')
                            ) 
                    Order_New.save()
                    if Order_New:
                        id_pedido = Order_New.id
                    else:
                        id_pedido = 0
                    #print("Encabezado: id", Order_New.id)
                    if Order_New:
                            detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo=codigo, usuario=request.user)
                            total_arts = 0
                            for item in detalle_tmp:

                                chk_prod= Product.objects.filter(product_name=item.product).first()
                                if chk_prod:
                                    producto = Product.objects.get(product_name=item.product)
                                    #print("Producto del Detalle:" , producto)
                                    if producto:
                                        Order_Det_New = OrderProduct(
                                                order = Order_New,
                                                user = request.user,
                                                product = producto,
                                                quantity = item.quantity,
                                                product_price = item.subtotal / item.quantity,  # EN LA IMPOSTARCION VIENE EL TOTAL NO PRECIO UNITARIO
                                                ordered = True,
                                                created_at = datetime.today(),
                                                updated_at = datetime.today()
                                            )
                                        Order_Det_New.save()
                                        if Order_Det_New:
                                            total_arts = total_arts + item.subtotal
                                        #Descuento Stock Articulos
                                        chk_prod.id = producto.id
                                        chk_prod.stock = chk_prod.stock - item.quantity
                                        chk_prod.save()

                        #Actualizo Total Items                    
                            Order_New.id = id_pedido
                            Order_New.order_total = total_arts
                            Order_New.save()

                    #Guardo al cliente
                    nuevo_usuario = Account.objects.filter(email=Order_New.email).first()
                    if not nuevo_usuario:
                        try:
                            usr_name= Order_New.email
                            i_end = usr_name.find('@')
                            usr_name = usr_name[1:i_end]
                            #print("usr_name",usr_name)
                            newUser = Account(
                                first_name      = Order_New.first_name,
                                last_name       = Order_New.last_name,
                                username        = usr_name,
                                email           = Order_New.email,
                                phone_number    = Order_New.dir_telefono,
                                date_joined     = datetime.today(),
                                last_login      = datetime.today(),
                                is_admin        = False,
                                is_staff        = False,
                                is_active       = False,
                                is_superadmin   = False
                            )
                            newUser.save()
                            #print("Se ingreso un nuevo cliente:", newUser.id)
                        except Exception as err:
                            print("Error no controlado: ",usr_name)
                            print(f"Unexpected {err=}, {type(err)=}")
                            pass


                    if pedidos_tmp:
                        print("1.Borro temp Pedidos:",id_pedido)
                        pedidos_tmp.id = id_pedido
                        pedidos_tmp.delete()
                    if detalle_tmp:
                        print("Borro temp Pedidos detalle")
                        detalle_tmp.delete()
                

                if pedidos_tmp:
                    print("2.Borro temp Pedidos",id_pedido)
                    pedidos_tmp.id = id_pedido
                    pedidos_tmp.delete()
                    detalle_tmp =  detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo=codigo, usuario=request.user)
                    if detalle_tmp:
                        detalle_tmp.delete()
                    
    #Si tiene acceso a PANEL
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    pedidos_tmp = ImportTempOrders.objects.filter(usuario = request.user).order_by('codigo')
    articulos_tmp = ImportTempOrdersDetail.objects.filter(usuario = request.user).order_by('codigo')
    cant_ok = pedidos_tmp.count()
    cant_error=0
    error_str = ""

    context = {
                'cant_ok':cant_ok,
                'permisousuario':permisousuario,
                'cant_error':cant_error,
                'error_str':error_str,
                'pedidos_tmp':pedidos_tmp,
                'articulos_tmp':articulos_tmp,
                                        
                }
    return render(request,'panel/importar_pedidos.html',context)

def guardar_tmp_pedidos_all(request):
      
    pedidos_tmp = ImportTempOrders.objects.filter(usuario = request.user).order_by('codigo')
    if pedidos_tmp:
        for pedido in pedidos_tmp:
            codigo = pedido.codigo
            pedidos_tmp = ImportTempOrders.objects.filter(usuario=request.user,codigo=codigo).first()
            if pedidos_tmp:
                id_pedido=pedidos_tmp.id
                order = Order.objects.filter(order_number=codigo)
                if not order:
                    #print("El pedido no existe, lo grabo")
                    user_account = Account.objects.get(email=request.user)
                    if user_account:
                        
                        Order_New = Order(
                            order_number=codigo,
                            first_name=pedidos_tmp.first_name,
                            last_name=pedidos_tmp.last_name,
                            email=pedidos_tmp.email,
                            created_at=pedidos_tmp.created_at,
                            fecha=pedidos_tmp.created_at,
                            updated_at=pedidos_tmp.updated_at,
                            user=user_account,
                            dir_telefono=pedidos_tmp.dir_telefono,
                            dir_calle=pedidos_tmp.dir_calle,
                            dir_nro =pedidos_tmp.dir_nro,
                            dir_localidad=pedidos_tmp.dir_localidad,
                            dir_provincia=pedidos_tmp.dir_provincia,
                            dir_cp = pedidos_tmp.dir_cp,
                            dir_obs = pedidos_tmp.dir_obs,
                            dir_correo= pedidos_tmp.dir_correo,
                            order_total = pedidos_tmp.order_total,
                            envio = 0,
                            status = "New",
                            is_ordered=True,
                            ip = request.META.get('REMOTE_ADDR')
                                ) 
                        Order_New.save()
                        if Order_New:
                            id_pedido = Order_New.id
                        else:
                            id_pedido = 0
                        #print("Encabezado: id", Order_New.id)
                        if Order_New:
                                detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo=codigo, usuario=request.user)
                                total_arts = 0
                                for item in detalle_tmp:

                                    chk_prod= Product.objects.filter(product_name=item.product).first()
                                    if chk_prod:
                                        producto = Product.objects.get(product_name=item.product)
                                        #print("Producto del Detalle:" , producto)
                                        if producto:
                                            Order_Det_New = OrderProduct(
                                                    order = Order_New,
                                                    user = request.user,
                                                    product = producto,
                                                    quantity = item.quantity,
                                                    product_price = item.subtotal / item.quantity,  # EN LA IMPOSTARCION VIENE EL TOTAL NO PRECIO UNITARIO
                                                    ordered = True,
                                                    created_at = datetime.today(),
                                                    updated_at = datetime.today()
                                                )
                                            Order_Det_New.save()
                                            if Order_Det_New:
                                                total_arts = total_arts + item.subtotal
                                            #Descuento Stock Articulos
                                            chk_prod.id = producto.id
                                            chk_prod.stock = chk_prod.stock - item.quantity
                                            chk_prod.save()

                            #Actualizo Total Items                    
                                Order_New.id = id_pedido
                                Order_New.order_total = total_arts
                                Order_New.save()

                        #Guardo al cliente
                        nuevo_usuario = Account.objects.filter(email=Order_New.email).first()
                        if not nuevo_usuario:
                            try:
                                usr_name= Order_New.email
                                i_end = usr_name.find('@')
                                usr_name = usr_name[1:i_end]
                                #print("usr_name",usr_name)
                                newUser = Account(
                                    first_name      = Order_New.first_name,
                                    last_name       = Order_New.last_name,
                                    username        = usr_name,
                                    email           = Order_New.email,
                                    phone_number    = Order_New.dir_telefono,
                                    date_joined     = datetime.today(),
                                    last_login      = datetime.today(),
                                    is_admin        = False,
                                    is_staff        = False,
                                    is_active       = False,
                                    is_superadmin   = False
                                )
                                newUser.save()
                                #print("Se ingreso un nuevo cliente:", newUser.id)
                            except Exception as err:
                                print("Error no controlado: ",usr_name)
                                print(f"Unexpected {err=}, {type(err)=}")
                                pass


                        if pedidos_tmp:
                            print("1.Borro temp Pedidos:",id_pedido)
                            pedidos_tmp.id = id_pedido
                            pedidos_tmp.delete()
                        if detalle_tmp:
                            print("Borro temp Pedidos detalle")
                            detalle_tmp.delete()
                    

                    if pedidos_tmp:
                        print("2.Borro temp Pedidos",id_pedido)
                        pedidos_tmp.id = id_pedido
                        pedidos_tmp.delete()
                        detalle_tmp =  detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo=codigo, usuario=request.user)
                        if detalle_tmp:
                            detalle_tmp.delete()
            


    return redirect('panel_pedidos','New') 

def panel_registrar_entrega(request,order_number=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    print("Sin acceso a ver pedidos")
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
        return render(request,'panel/login.html',)

#Si tiene acceso a PANEL

    if accesousuario.codigo.codigo =='PEDIDOS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if order_number:
            orden = Order.objects.get(order_number=order_number)
        context = {
            'orden':orden,
            'permisousuario':permisousuario,
        
           }
        print(orden)
        return render(request,'panel/registrar_entrega.html',context) 

    return render(request,'panel/login.html',)

def panel_confirmar_entrega(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    print("Sin acceso a ver pedidos")
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
        return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL

    if accesousuario.codigo.codigo =='PEDIDOS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if request.method =="POST":
            order_number = request.POST.get("order_number")
            if order_number:
                order = Order.objects.get(order_number=order_number)
                if order:
                    entrega = OrderShipping.objects.filter(order=order.id)
                    if not entrega:
                        
                        new_entrega = OrderShipping(
                            order = order,
                            fecha = datetime.today(),
                            user = request.user
                            )
                        new_entrega.save()
                        print("Guardo entrega")
                        status = "Entregado"
                        if order:
                            order.status = status
                            order.save()
                            print("Grabo etado pedido")
                    else:
                            print("Ya se entrego", order_number)

            return redirect('panel_pedidos','Cobrado') 

    return render(request,'panel/login.html',)

def panel_pedidos_eliminar_pago(request,order_number=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='PEDIDOS':
        print("---->>>>>>>Eliminar: ",order_number)
        try:
            if order_number:
                print("--->", order_number)
                ordenes = Order.objects.get(order_number=order_number)
                if ordenes:
                    id_orden = ordenes.id
                    id_pago = ordenes.payment.id
                    print("ID Pago -->", id_pago)
                    print("ID ORden --> ", id_orden)
                    pago = Payment.objects.get(id=id_pago)
                    id_pago = pago.id
                    if pago:
                       
                        movimiento = Movimientos.objects.get(ordernumber=id_orden)
                        if movimiento:
                            id_mov = movimiento.id
                            print("Mov --> ",id_mov )
                            movimiento.id = id_mov
                            movimiento.delete()
                        else:
                            print("Error al eliminar el movimiento")
                        ordenes.id = id_orden
                        ordenes.payment = ""
                        ordenes.save()
                        pago.id = id_pago
                        pago.delete()
                    else:
                        print("Error en el medio de pago")
                else:
                    print("No se encontro el pedido")
              
                messages.success(request,"Pago Eliminado.")
            else:
                print("No se encontro el Nro de Orden")        
            return redirect('panel_pedidos','New')
        except Exception as err:
            error_str=  f"Unexpected {err=}, {type(err)=}"
            messages.error(request,"Error Exception:" + error_str,'red')
            return redirect('panel_pedidos','New')

    return render(request,'panel/login.html',)

def panel_pedidos_eliminar_entrega(request,order_number=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PEDIDOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL 
    if accesousuario.codigo.codigo =='PEDIDOS':
        print(">>>>Eliminar Entrega: ",order_number)
        try:
            if order_number:
                print("--->", order_number)
                ordenes = Order.objects.get(order_number=order_number)
                if ordenes:
                    id_ordenes = ordenes.id
                    ordenes.id = ordenes.id
                    ordenes.status = "Cobrado"
                    ordenes.save()                    
                    entrega = OrderShipping.objects.get(order=id_ordenes)
                    if entrega:
                        entrega.order = ordenes
                        entrega.delete()
                        messages.success(request,"Entrega Eliminado.")

            else:
                print("No se encontro el Nro de Orden")        
                return redirect('panel_pedidos','New')
        except Exception as err:
            error_str=  f"Unexpected {err=}, {type(err)=}"
            messages.error(request,"Error Exception:" + error_str,'red')
            return redirect('panel_pedidos','Cobrado')
        return redirect('panel_pedidos','Cobrado')

    return render(request,'panel/login.html',)

def panel_movimientos_transf(request,idtrans=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='TRANSFERENCIAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='TRANSFERENCIAS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        if request.method == "GET":
            if idtrans:
                trans = Transferencias.objects.filter(pk=idtrans).first()
            else:
                trans = []

            cuentas = Cuentas.objects.all()
            fecha = datetime.today()
            fecha = fecha.strftime("%d/%m/%Y")

            context = {
                'trans':trans,
                'permisousuario':permisousuario,
                'cuentas':cuentas,
                'fecha':fecha,
                        
            }

            return render(request,'panel/registrar_transferencia.html',context) 

        if request.method =="POST":
           
            fecha=request.POST.get("fecha")
            cliente=request.POST.get("cliente")
            cuenta_origen=request.POST.get("cuenta_origen")
            cuenta_destino=request.POST.get("cuenta_destino")
            monto_origen=request.POST.get("monto_origen")
            monto_destino=request.POST.get("monto_destino")
            conversion=request.POST.get("conversion")
            observaciones=request.POST.get("observaciones")
            fecha_a_datetime = datetime.strptime(fecha, '%d/%m/%Y')

            print(fecha,cliente,cuenta_origen,cuenta_destino,monto_origen,monto_destino,conversion,observaciones)
            
            if idtrans:
                #Si modician Elimino y creo de nuevo
                trans = Transferencias.objects.filter(pk=idtrans).first()
                if trans:
                    idtransfer=trans.id
                    print("idtrans",idtransfer)
                    trans.delete()
                    mov1 = Movimientos.objects.filter(idtransferencia=idtransfer).all()
                    if mov1:
                        mov1.delete()
                  

            # ORIGEN
            rs_cuenta1 = Cuentas.objects.filter(id=cuenta_origen).get()
            rs_operacion1 = Operaciones.objects.filter(codigo="EGR").get()  #EGRESO
            

            #DESTINO
            rs_cuenta2 = Cuentas.objects.filter(id=cuenta_destino).get()
            rs_operacion2 = Operaciones.objects.filter(codigo="ING").get()  #INGRESO
           

            rs_operacion3 = Operaciones.objects.filter(codigo="TRF").get()  #TRANSFERENCIA

            #TRANSFERENCIA 
            trans = Transferencias (
                fecha = fecha_a_datetime,
                cliente = cliente,
                movimiento=rs_operacion3,
                cuenta_origen = rs_cuenta1,
                cuenta_destino = rs_cuenta2,
                monto_origen=monto_origen,
                conversion=conversion,
                monto_destino=monto_destino,
                observaciones = observaciones
                )
            trans.save()
            if trans:
                idtrans = trans.id
            print("Nueva Transfeencia: ", idtrans)

            if float(monto_origen) > 1:
                print(rs_operacion1.codigo)
                if rs_operacion1.codigo=="EGR":
                    monto_origen = float(monto_origen) * -1
                    print(monto_origen)
            mov = Movimientos (
                fecha       =  fecha_a_datetime,
                cliente     = cliente,
                cuenta      = rs_cuenta1,
                monto       = monto_origen,
                idtransferencia = idtrans,
                movimiento  = rs_operacion1,
                observaciones = "Transf: " + str(idtrans) + " - " +  observaciones
                )
            mov.save()
            if mov:
                id_mov_origen = mov.id
                print("Add Mov Origen", id_mov_origen)


                mov2 = Movimientos (
                    fecha       =  fecha_a_datetime,
                    cliente     = cliente,
                    cuenta      = rs_cuenta2,
                    idtransferencia = idtrans,
                    monto       = monto_destino,
                    movimiento  = rs_operacion2,
                    observaciones = "Transf: " + str(idtrans) + " - " +  observaciones
                    )
                mov2.save()
                if mov2:
                    id_mov_destino = mov2.id
                    print("Add Mov Destino", id_mov_destino)
                
                #ACTUALIZO LOS NRO DE MOVIMIENTOS GENERADOS.
                trans = Transferencias (
                    id = idtrans,
                    fecha = fecha_a_datetime,
                    cliente = cliente,
                    movimiento=rs_operacion3,
                    cuenta_origen = rs_cuenta1,
                    cuenta_destino = rs_cuenta2,
                    monto_origen=monto_origen,
                    conversion=conversion,
                    monto_destino=monto_destino,
                    observaciones = observaciones,
                    idmov_origen = mov,
                    idmov_destino = mov2
                    )
                trans.save()

            return redirect('panel_transferencias') 


    return render(request,'panel/login.html',)

def registrar_movimiento(request,idmov=None):
        
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='MOVIMIENTOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='MOVIMIENTOS':
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')


        if request.method == "GET":
            if idmov:
                mov = Movimientos.objects.filter(id=idmov).first()
                print("getid",mov)
            else:
                mov = []

            operaciones= Operaciones.objects.all()
            cuentas = Cuentas.objects.all()
            fecha = datetime.today()

            context = {
                'mov':mov,
                'operaciones':operaciones,
                'permisousuario':permisousuario,
                'cuentas':cuentas,
                'fecha':fecha,
                        
            }

            return render(request,'panel/registrar_movimiento.html',context) 

        if request.method=="POST":

            idmov=request.POST.get("idmov")
            fecha=request.POST.get("fecha")
            cliente=request.POST.get("cliente")
            cuenta=request.POST.get("cuenta")
            monto=request.POST.get("monto")
            tipo_mov=request.POST.get("tipo_mov")
            observaciones=request.POST.get("observaciones")

            rs_cuenta = Cuentas.objects.filter(id=cuenta).get()
            rs_operacion = Operaciones.objects.filter(codigo=tipo_mov).get()
           
            
            fecha_a_datetime = datetime.strptime(fecha, '%d/%m/%Y')
            
            
            if float(monto) > 1:
                if rs_operacion.codigo=="EGR":
                    monto = float(monto) * -1
                   
            if idmov: 
                movimiento = Movimientos.objects.filter(pk=idmov).get()
                if movimiento:
                    mov = Movimientos (
                        id          = idmov,
                        fecha       =  fecha_a_datetime,
                        cliente     = cliente,
                        cuenta      = rs_cuenta,
                        monto       = monto,
                        movimiento  = rs_operacion,
                        observaciones = observaciones
                        )
                    mov.save()
                    print("Update", idmov)
            else:
                mov = Movimientos (
                    fecha       =  fecha_a_datetime,
                    cliente     = cliente,
                    cuenta      = rs_cuenta,
                    monto       = monto,
                    movimiento  = rs_operacion,
                    observaciones = observaciones
                    )
                mov.save()
                print("New")

            #print("fecha",fecha)
            #print("cliente",cliente)
            #print("cuenta",rs_cuenta.id, rs_cuenta.moneda.id)
            #print("monto",monto)
            #print("tipo_mov",tipo_mov)
            #print("observaciones",observaciones)

        return redirect('panel_movimientos') 
    
    
    return render(request,'panel/login.html',)

def panel_transferencias_eliminar(request,idtrans=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='TRANSFERENCIAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='TRANSFERENCIAS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        if request.method == "GET":
            if idtrans:
                trans = Transferencias.objects.filter(pk=idtrans).first()
            else:
                trans = []

         
            context = {
                'trans':trans,
                'permisousuario':permisousuario
            }

            return render(request,'panel/eliminar_transferencia.html',context) 

        if request.method =="POST":
           
            #idtransfer=request.POST.get("idtransf")
            print("Eliminar transferencia -->",idtrans)
            if idtrans:
                #Si modician Elimino y creo de nuevo
                trans = Transferencias.objects.filter(pk=idtrans).first()
                if trans:
                    idtransfer=trans.id
                    print("idtrans",idtransfer)
                    trans.delete()
                    mov1 = Movimientos.objects.filter(idtransferencia=idtransfer).all()
                    if mov1:
                        mov1.delete()
                  

            
            return redirect('panel_transferencias') 


    return render(request,'panel/login.html',)

def panel_movimiento_eliminar(request,idmov=None):
        
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='MOVIMIENTOS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                    return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='MOVIMIENTOS':
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')


        if request.method == "GET":
            if idmov:
                mov = Movimientos.objects.filter(id=idmov).first()
                print("getid",mov)
            else:
                mov = []

            context = {
                'mov':mov,
                'permisousuario':permisousuario
            }

            return render(request,'panel/eliminar_movimiento.html',context) 

        if request.method=="POST":
            print(idmov)
            if idmov: 
                movimiento = Movimientos.objects.filter(pk=idmov).get()
                if movimiento: 
                    movimiento.delete()
                  
        return redirect('panel_movimientos') 
    
    
    return render(request,'panel/login.html',)
