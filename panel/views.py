from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from accounts.models import AccountPermition,Permition
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from store.models import Product,Variation
from orders.models import Order, OrderProduct,Payment,OrderShipping
from category.models import Category, SubCategory
from accounts.models import Account, UserProfile    
from contabilidad.models import Cuentas, Movimientos,Operaciones, Monedas, Transferencias
from panel.models import ImportTempProduct, ImportTempOrders, ImportTempOrdersDetail

from accounts.forms import UserForm, UserProfileForm
from django.db.models import Q, Sum, Count,Max , DecimalField
from django.db.models.functions import Round
from django.http import HttpResponse
from slugify import slugify
from datetime import timedelta,datetime


import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders



from dateutil.relativedelta import relativedelta
from django.conf import settings

from urllib.parse import unquote

from django.db import connection

import xlwt,xlrd
import csv


import os
# Create your views here.
def monthToNum(shortMonth):
    return {
            'Enero': 1,
            'Febrero': 2,
            'Marzo': 3,
            'Abril': 4,
            'Mayo': 5,
            'Junio': 6,
            'Julio': 7,
            'Agosto': 8,
            'Septiembre': 9, 
            'Octubre': 10,
            'Noviembre': 11,
            'Diciembre': 12
    }[shortMonth]

def NumTomonth(shortMonth):
    return {
            1:'Enero',
            2: 'Febrero',
            3:'Marzo',
            4:'Abril',
            5: 'Mayo',
            6: 'Junio',
            7 :'Julio',
            8 : 'Agosto',
            9 : 'Septiembre', 
            10 : 'Octubre',
            11 : 'Noviembre',
            12 : 'Diciembre'
    }[shortMonth]

def search_lookup(request,keyword=None,order_number=None):

    product_count=0
    products = []

    keyword = unquote(keyword)
    keyword = keyword.replace(' ','-')
    print("Buscar:", keyword)
    if keyword:
        if keyword == "all":
            products = Product.objects.order_by('product_name').all()
            product_count = products.count()
        else:
            products = Product.objects.order_by('product_name').filter(Q(product_name__icontains=keyword) | Q(slug__icontains=keyword))
            product_count = products.count()
    else:
        products = Product.objects.order_by('product_name').all()
        product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,
        'keyword':keyword,
        'order_number':order_number,
    }
    return render(request, 'panel/productos_lookup.html' , context)

def validar_permisos(request,codigo=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  AccountPermition.objects.filter(user=request.user, codigo__codigo =codigo,modo_ver=True).first()
            if not accesousuario:
                print("No tiene permiso para el modulo: ", codigo)
                return False  
        else:
            print("Usuario no registrado: ", codigo)
            return False
    except ObjectDoesNotExist:
            print("Excepcion: ", codigo)
            return False
            
    if accesousuario.codigo.codigo ==codigo:
        print("Acceso modulo:  ", codigo)
        return True
    else:
        print("No tiene permiso para el modulo: ", codigo)
        return False

def panel_home(request):

    
    if validar_permisos(request,'PANEL'):
        
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        context = {
            'permisousuario':permisousuario
            }
        print("Acceso Panel")

        return render (request,"panel/base.html",context)
    else:
        return render (request,"panel/login.html")

def dashboard_ventas(request):
   
    if validar_permisos(request,'DASHBOARD VENTAS'):
        
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
        pedidos = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('status').annotate(cantidad=Count('order_number')).order_by('status')
        
        clientes = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('last_name','first_name').annotate(total=
                     Round(
                Sum('order_total'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('-order_total')[:5]

        
        items_pedidos = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta])
        items = OrderProduct.objects.filter(order__in=items_pedidos).values('product__product_name').annotate(cantidad=Sum('quantity')).order_by('-quantity')[:5]
       
        hist_pedidos = []

        for i in range(1, 13): 
            payments_months = Order.objects.filter(fecha__month = i)
            month_earnings = round(sum([Order.order_total for Order in payments_months]))
            hist_pedidos.append(month_earnings)


        
        yr = int(datetime.today().strftime('%Y'))
        dt = 1
        mt = int(datetime.today().strftime('%m'))
        lim_fecha_desde = datetime(yr,mt,dt)
        if mt==12:
            mt=1
            yr+=1
        else:
            mt = int(mt) + 1
        
        lim_fecha_hasta = datetime(yr,mt,dt)
        lim_fecha_hasta = lim_fecha_hasta + timedelta(days=-1)
      
       
        form = []
        context = {
            'permisousuario':permisousuario,
            'hist_pedidos':hist_pedidos,
            'items': items,
            #'cuentas':cuentas,
            'pedidos':pedidos,
            'clientes':clientes,
            'form': form,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta,
            'lim_fecha_desde':lim_fecha_desde,
            'lim_fecha_hasta':lim_fecha_hasta
           
            }
        print("Acceso Panel")
        return render (request,"panel/dashboard_ventas.html",context)
    else:
        return render (request,"panel/login.html")
          
def dashboard_cuentas(request):
    
    if validar_permisos(request,'DASHBOARD CUENTAS'):

        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")

        # POR DEFAULT TOMAMOS EL MES CORRIENTE
        yr = int(datetime.today().strftime('%Y'))
        dt = 1
        mt = int(datetime.today().strftime('%m'))
        lim_fecha_desde = datetime(yr,mt,dt)
 
        mt = int(mt) + 1
        lim_fecha_hasta = datetime(yr,mt,dt)
        lim_fecha_hasta = lim_fecha_hasta + timedelta(days=-1)

        if not fecha_1 and not fecha_2 :
            fecha_desde = lim_fecha_desde
            fecha_hasta = lim_fecha_hasta

        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')


        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        saldos = Movimientos.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('cuenta__nombre').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2)))
        
        mov_ing = Operaciones.objects.filter(codigo='ING').first()
        cuentas = Movimientos.objects.filter(fecha__range=[fecha_desde,fecha_hasta],movimiento=mov_ing).values('cuenta__nombre').annotate(porcentaje=
         Round(
                Sum('monto') * 100 / Max('cuenta__limite'),
                output_field=DecimalField(max_digits=12, decimal_places=2)))
        
        form = []
        context = {
            'permisousuario':permisousuario,
            'data': saldos,
            'cuentas':cuentas,
            'form': form,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta,
            'lim_fecha_desde':lim_fecha_desde,
            'lim_fecha_hasta':lim_fecha_hasta
           
            }
        print("Acceso Panel")
        #return render (request,"panel/dashboard_cuentas.html",context)
        return render (request,"panel/dashboard_cuentas.html",context)
    else:
        return render (request,"panel/login.html")

def dashboard_resultados(request):

    if validar_permisos(request,'DASHBOARD RESULTADOS'):
        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")

        # POR DEFAULT TOMAMOS EL MES CORRIENTE
        yr = int(datetime.today().strftime('%Y'))
        dt = 1
        mt = int(datetime.today().strftime('%m'))
        lim_fecha_desde = datetime(yr,mt,dt)
 
        mt = int(mt) + 1
        lim_fecha_hasta = datetime(yr,mt,dt)
        lim_fecha_hasta = lim_fecha_hasta + timedelta(days=-1)

        if not fecha_1 and not fecha_2 :
            fecha_desde = lim_fecha_desde
            fecha_hasta = lim_fecha_hasta

        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')


        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        saldos = Movimientos.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('cuenta__nombre','cuenta__moneda').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2)))
        print(saldos)
        context = {
            'permisousuario':permisousuario,
            'saldos':saldos,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta
        }
        return render (request,"panel/dashboard.html",context)
    else:
        return render (request,"panel/login.html")  

def panel_product_list_category(request):
    
    if validar_permisos(request,'PRODUCTO'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categorias = Category.objects.all()
        catalogo = Product.objects.all().order_by('product_name')
        cantidad = catalogo.count()
        categoria=0
       
    
        if request.method =="GET":
            catalogo = Product.objects.all().order_by('product_name')
            cantidad = catalogo.count()
    
        if request.method =="POST":
        
            category = request.POST.get("category")
            categoria=int(category)
           

            print("category",category)
         

            if category:
                if category=='0':
                    catalogo = Product.objects.all().order_by('product_name')
                    cantidad = catalogo.count()
                else:
                    catalogo = Product.objects.filter(category=category).order_by('product_name')
                    cantidad = catalogo.count()
  

        context = {
            'catalogo':catalogo,
            'categorias':categorias,
            'permisousuario':permisousuario,
            'cantidad':cantidad,
            'categoria':categoria,
          
        }
       
        return render(request,'panel/lista_productos.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_reporte_articulos(request):
    
   
    if validar_permisos(request,'REPORTES'):
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categorias = Category.objects.all()
        subcategoria = []
       

        catalogo = Product.objects.filter().all().order_by('product_name')
        cantidad = catalogo.count()
        context = {
            'catalogo':catalogo,
            'categorias':categorias,
            'subcategoria':subcategoria,
            'permisousuario':permisousuario,
            'cantidad':cantidad
        }
       
        return render(request,'panel/lista_productos.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_product_list(request):
    
   
    if validar_permisos(request,'PRODUCTO'):
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categorias = Category.objects.all()
        subcategoria = []
       

        catalogo = Product.objects.filter().all().order_by('product_name')
        cantidad = catalogo.count()
        context = {
            'catalogo':catalogo,
            'categorias':categorias,
            'subcategoria':subcategoria,
            'permisousuario':permisousuario,
            'cantidad':cantidad
        }
       
        return render(request,'panel/lista_productos.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_product_detalle(request,product_id=None):
    
    if validar_permisos(request,'PRODUCTO'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        if product_id:
            product = get_object_or_404(Product, id=product_id)

            producto = Product.objects.get(product_name=product.product_name)
            categorias = Category.objects.all()
            variantes = Variation.objects.filter(product=product)
            subcategoria = SubCategory.objects.filter(category=producto.category).all()

            print(subcategoria)

        else:
            categorias = Category.objects.all()
            producto = []
            variantes = []
            subcategoria=[]

        context = {
            'producto':producto,
            'permisousuario':permisousuario,
            'categorias': categorias,
            'subcategoria':subcategoria,
            'variantes':variantes,
        }
    
        return render(request,'panel/productos_detalle.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_list(request,status=None):
    
    if validar_permisos(request,'PEDIDOS'):
        if not status:
            status='New'

        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")     
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=15) 
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

        cuenta = Cuentas.objects.filter()


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
            "fecha_hasta":fecha_hasta,
            "cuenta":cuenta
             
            


        }
        return render(request,'panel/lista_pedidos.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_detalle(request,order_number=None):

    if validar_permisos(request,'PEDIDOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        ordenes = Order.objects.get(order_number=order_number)
        ordenes_detalle = OrderProduct.objects.filter(order_id=ordenes.id).annotate(subtotal=
            Round(
                Sum('product_price')*Sum('quantity'),2
                ))
                
        idcuenta = ordenes.cuenta
        if idcuenta>0:
            cuenta = Cuentas.objects.get(id=idcuenta)
        else:
            cuenta= []
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
            'entregado':entregado,
            'cuenta':cuenta
        }
        
        return render(request,'panel/pedidos_detalle.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_enviar_factura(request,order_number=None):

    if validar_permisos(request,'PEDIDOS FACTURA'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        pedido = Order.objects.get(order_number=order_number)
        archivo=""     
        if request.method =="POST":
            print("Cargando factura...")
            try:
                if request.FILES["imgFile"]:
                    fileitem = request.FILES["imgFile"]
                    # check if the file has been uploaded
                    archivo=fileitem
                    if fileitem.name:
                        # strip the leading path from the file name
                        fn = os.path.basename(fileitem.name)
                        # open read and write the file into the server
                        open(f"media/facturas/{fn}", 'wb').write( fileitem.file.read())  
                        #pdf_root = f"media/facturas/{fileitem}"
                        pdf_root = f"{fileitem}"
                                
            except:
                 pass

            archivo = pdf_root
            print("Cargando factura...",pdf_root)
            if archivo:
                
                if pedido:
                    if  pedido.email:


                        print("Enviado a:", pedido.email)
                        mensaje = MIMEMultipart()
                        mensaje['From']=  settings.EMAIL_HOST_USER 
                        mensaje['To']=pedido.email 
                        mensaje['Subject']='Factura de su compra ' + str(order_number)

                        mensaje.attach(MIMEText("Gracias por su compra.  Aqui le enviamos su factura",'plain'))
                        
                        archivo_adjunto = open('media/facturas/' + archivo,'rb')

                        adjunto_MIME = MIMEBase('aplication','octet-stream')
                        adjunto_MIME.set_payload((archivo_adjunto).read())
                        encoders.encode_base64(adjunto_MIME)

                        adjunto_MIME.add_header('Content-Disposition',"attachment; filename= %s" %archivo)
                        mensaje.attach(adjunto_MIME)

                        try:

                            session_smtp = smtplib.SMTP(settings.EMAIL_HOST ,settings.EMAIL_PORT)
                            session_smtp.starttls()
                            session_smtp.login(settings.EMAIL_HOST_USER ,settings.EMAIL_HOST_PASSWORD)
                            texto = mensaje.as_string()
                            session_smtp.sendmail(settings.EMAIL_HOST_USER,pedido.email,texto)
                            session_smtp.quit()
                           
                            messages.success(request,"Factura enviada con exito.")
                            return redirect('panel_pedidos','Cobrado')
                             
                        except Exception as err:
                            error_str=  f"Unexpected {err=}, {type(err)=}"
                            messages.error(request,"Error Exception:" + error_str,'red')
                
                try:
                    os.remove(archivo)
                except:
                    pass                        
        
        context = {
            'pedido':pedido,
            'permisousuario':permisousuario,
        }
        
        return render(request,'panel/enviar_factura_email.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_enviar_tracking(request,order_number=None):

    if validar_permisos(request,'PEDIDOS FACTURA'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        pedido = Order.objects.get(order_number=order_number)
        archivo=""     
        if request.method =="POST":
            print("Cargando imagen...")
            try:
                if request.FILES["imgFile"]:
                    fileitem = request.FILES["imgFile"]
                    # check if the file has been uploaded
                    archivo=fileitem
                    if fileitem.name:
                        # strip the leading path from the file name
                        fn = os.path.basename(fileitem.name)
                        # open read and write the file into the server
                        open(f"media/facturas/{fn}", 'wb').write( fileitem.file.read())  
                        #pdf_root = f"media/facturas/{fileitem}"
                        pdf_root = f"{fileitem}"
                                
            except:
                 pass

            archivo = pdf_root
            print("Cargando imagen...",pdf_root)
            if archivo:
                
                if pedido:

                    nro_tracking = request.POST.get("tracking")
                    print("Save Tracking table")
                        #Guardar tracking
                    pedido.fecha_tracking = datetime.now()
                    pedido.nro_tracking = nro_tracking
                    pedido.save()

                    

                    if  pedido.email:

                        
                        print("Enviado a:", pedido.email)
                        mensaje = MIMEMultipart()
                        mensaje['From']=  settings.EMAIL_HOST_USER 
                        mensaje['To']=pedido.email 
                        mensaje['Subject']='Seguimiento del pedido ' + str(order_number)

                        mensaje.attach(MIMEText("Gracias por su compra.  Aqui le enviamos el seguimiento de su pedido junto con la foto del pedido. https://www.correoargentino.com.ar/formularios/e-commerce?id="+ str(nro_tracking),'plain'))
                        
                        archivo_adjunto = open('media/facturas/' + archivo,'rb')

                        adjunto_MIME = MIMEBase('aplication','octet-stream')
                        adjunto_MIME.set_payload((archivo_adjunto).read())
                        encoders.encode_base64(adjunto_MIME)

                        adjunto_MIME.add_header('Content-Disposition',"attachment; filename= %s" %archivo)
                        mensaje.attach(adjunto_MIME)

                        try:

                            session_smtp = smtplib.SMTP(settings.EMAIL_HOST ,settings.EMAIL_PORT)
                            session_smtp.starttls()
                            session_smtp.login(settings.EMAIL_HOST_USER ,settings.EMAIL_HOST_PASSWORD)
                            texto = mensaje.as_string()
                            session_smtp.sendmail(settings.EMAIL_HOST_USER,pedido.email,texto)
                            session_smtp.quit()
                           
                            messages.success(request,"Tracking enviado con exito.")
                            return redirect('panel_pedidos','Cobrado')
                             
                        except Exception as err:
                            error_str=  f"Unexpected {err=}, {type(err)=}"
                            messages.error(request,"Error Exception:" + error_str,'red')
                
                try:
                    os.remove(archivo)
                except:
                    pass                        
        

        context = {
            'pedido':pedido,
            'permisousuario':permisousuario,
        }
        
        return render(request,'panel/enviar_tracking_email.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_enviar_datos_cuenta(request,order_number=None):


    print("panel_pedidos_enviar_datos_cuenta")
    if validar_permisos(request,'PEDIDOS'):
        
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        pedido = Order.objects.get(order_number=order_number)
        if request.method =="POST":
            cuenta =  request.POST.get("cuenta")
            documento = request.POST.get("documento")
            nrocuenta = request.POST.get("nrocuenta")
            cbu = request.POST.get("cbu")
            cuil = request.POST.get("cuil")
            alias = request.POST.get("alias")
            envio = request.POST.get("envio")
            total = request.POST.get("total")
            subtotal = request.POST.get("subtotal")
            
            envio = envio.replace(",",".")
            total = total.replace(",",".")
            subtotal = subtotal.replace(",",".")


         
            if pedido:
                #Actualizo el cotos del envio y la cuenta asociada para el pago
                

                Order_New = Order(
                    id = pedido.id,
                    order_number=pedido.order_number,
                    first_name=pedido.first_name,
                    last_name=pedido.last_name,
                    email=pedido.email,
                    created_at=pedido.created_at,
                    fecha=pedido.fecha,
                    updated_at=pedido.updated_at,
                    dir_telefono=pedido.dir_telefono,
                    dir_calle=pedido.dir_calle,
                    dir_nro =pedido.dir_nro,
                    dir_localidad=pedido.dir_localidad,
                    dir_provincia=pedido.dir_provincia,
                    dir_cp = pedido.dir_cp,
                    dir_obs = pedido.dir_obs,
                    dir_correo= pedido.dir_correo,
                    order_total = total,
                    envio = envio,
                    status = pedido.status,
                    is_ordered=True,
                    ip = request.META.get('REMOTE_ADDR'),
                    total_peso=pedido.total_peso,
                    cuenta=cuenta
                    ) 
                Order_New.save()
                
                if  pedido.email:
                    print("Enviado a:", pedido.email)
                    mensaje = MIMEMultipart()
                    mensaje['From']=  settings.EMAIL_HOST_USER 
                    mensaje['To']=pedido.email 
                    mensaje['Subject']='Lifche - Datos de pago  ' + str(order_number)

                    #mensaje.attach(MIMEText("Gracias por su compra.  Aqui le enviamos los datos para transferir",'plain'))
                    
                    msg_content = '''
                    <html><body><p><table>
                    <tr>
                        <td>Hola,<strong> '''+ str(pedido.last_name)+  ''', '''  + str(pedido.first_name)+  ''' </strong></td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>Adjuntamos datos de transferencia. </td>
                    </tr>
                    <tr>
                        <td> Subtotal: $ '''  + str(subtotal) + ''' </td>
                    </tr>
                        <td> Envío  $ '''  + str(envio) + ''' </td>
                    </tr>
                    <tr>
                        <td>Total a abonar : <strong>$ ''' + str(total) + ''' </strong></td>
                    </tr>
                    <tr>
                        <td></td>
                    </tr>
                    <tr>
                        <td></td>            
                    </tr>
                    <tr>
                        <td>Documento: ''' + str(documento) + ''' </td>
                    </tr>
                    <tr>
                        <td>Cuenta:  ''' + str(nrocuenta) + '''</td>
                     </tr>
                    <tr>
                        <td>CBU: ''' + str(cbu) + '''</td>
                    </tr>
                    <tr>
                        <td>CUIL: ''' + str(cuil) + '''</td>
                     </tr>
                    <tr>
                        <td>Alias: ''' + str(alias) + '''</td>
                     </tr>
                    <tr>
                        <td></td>
                        <td></td>            
                    </tr>
                    <tr>
                        <td>Muchas gracias por su compra.</td>
                    </tr>
                    <tr>
                        <td></td>
                        <td>Lifche.</td>
                    </tr>

                    </table></p></body></html>'''
                    mensaje.attach(MIMEText((msg_content), 'html'))

                    #with open('img/lifche.jpg', 'rb') as image_file:
                    #    image = MIMEImage(image_file.read())
                    #image.add_header('Content-ID', '<picture@example.com>')
                    #image.add_header('Content-Disposition', 'inline', filename='image.jpg')
                    #mensaje.attach(image)



                    try:

                        session_smtp = smtplib.SMTP(settings.EMAIL_HOST ,settings.EMAIL_PORT)
                        session_smtp.starttls()
                        session_smtp.login(settings.EMAIL_HOST_USER ,settings.EMAIL_HOST_PASSWORD)
                        texto = mensaje.as_string()
                        session_smtp.sendmail(settings.EMAIL_HOST_USER,pedido.email,texto)
                        session_smtp.quit()
                        
                        messages.success(request,"Datos enviados con exito.")
                        return redirect('panel_pedidos','New')
                            
                    except Exception as err:
                        error_str=  f"Unexpected {err=}, {type(err)=}"
                        messages.error(request,"Error Exception:" + error_str,'red')

        context = {
            'pedido':pedido,
            'permisousuario':permisousuario,
        }
        
        return render(request,'panel/enviar_datos_pago.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_detalle_edit(request,order_number=None):

    if validar_permisos(request,'PEDIDOS EDIT'):

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
        
        return render(request,'panel/pedido_detalle_edit.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_confirmacion_eliminar(request,order_number=None):

    if validar_permisos(request,'PEDIDOS DEL'):

        context = {
            'order_number':order_number
        }
        print("panel_pedidos_confirmacion_eliminar",order_number)
        return render(request,'panel/pedido_eliminar.html',context) 
    else:
        return render (request,"panel/login.html")
   
def panel_pedidos_eliminar(request,order_number=None):

    if validar_permisos(request,'PEDIDOS DEL'):
        print("Eliminar",order_number)
        if order_number:
                ordenes = Order.objects.get(order_number=order_number)
                if ordenes:
                    ordenes_detalle = OrderProduct.objects.filter(order_id=ordenes.id)
                    if ordenes_detalle:
                        ordenes_detalle.delete()
                ordenes.delete()
                messages.success(request,"Pedido eliminado con exito.")
        
        return redirect('panel_pedidos','New')
    else:
        return render (request,"panel/login.html")

def panel_pedidos_del_detalle(request,order_number,id_linea):

    if validar_permisos(request,'PEDIDOS EDIT'):

        print("order_number",order_number)
        print("idlinea",id_linea)

        #articulo = Product.objects.filter(product_name=producto).first()
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.get(order_id=order.id,pk=id_linea)
    
        if ordered_products:           
            ordered_products = OrderProduct(
                id = ordered_products.id,
            )        
            ordered_products.delete()
            panel_recalcular_totales(order_number)
            messages.success(request,"Articulo eliminado con exito.")
            

        panel_pedidos_detalle(request,order_number)          
        return redirect('panel_pedidos_detalle',  str(order_number))  
    else:
        return render (request,"panel/login.html")
        
def panel_pedidos_save_detalle(request):

    if validar_permisos(request,'PEDIDOS EDIT'):

       
        if request.method =="POST":
            
            order_number = request.POST.get("edit_order_number")
            id_linea = request.POST.get("edit_item_id")
            cantidad = request.POST.get("edit_quantity")
            precio = request.POST.get("edit_precio")

            print("cantidad",cantidad,"order_number",order_number)
            if cantidad:
                if precio:
                    if order_number:
                        
                        order = Order.objects.get(order_number=order_number, is_ordered=True)
                        ordered_products = OrderProduct.objects.get(order_id=order.id,pk=id_linea)
                    
                        if ordered_products:           
                            ordered_products = OrderProduct(
                                id = ordered_products.id,
                                quantity = cantidad,
                                product_price = precio,
                                order = ordered_products.order, 
                                payment = ordered_products.payment,
                                user =ordered_products.user,
                                product=ordered_products.product,
                                ordered=ordered_products.ordered,
                                created_at = ordered_products.created_at,
                                updated_at = datetime.today()
                            )        
                            ordered_products.save()
                            panel_recalcular_totales(order_number)
                            messages.success(request,"Articulo guardado con exito.")
                    

                        panel_pedidos_detalle(request,order_number)          
                        return redirect('panel_pedidos_detalle',  str(order_number))  
            else:
                pass

    else:
        return render (request,"panel/login.html")

def panel_pedidos_save_enc(request):

        print("panel_pedidos_save_enc")
        if request.method =="POST":
            
            order_number = request.POST.get("order_number")
            fecha = request.POST.get("fecha")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            dir_calle = request.POST.get("dir_calle")
            dir_nro = request.POST.get("dir_nro")
            dir_localidad = request.POST.get("dir_localidad")
            dir_provincia = request.POST.get("dir_provincia")
            dir_telefono = request.POST.get("dir_telefono")
            email = request.POST.get("email")
            
            fecha = datetime.strptime(fecha, '%d/%m/%Y')
            
            order = Order.objects.get(order_number=order_number)
            if order:
                Order_New = Order(
                    id = order.id,
                    order_number=order_number,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    created_at=order.created_at,
                    fecha=fecha,
                    updated_at=order.updated_at,
                    #user=user_account,
                    dir_telefono=dir_telefono,
                    dir_calle=dir_calle,
                    dir_nro =dir_nro,
                    dir_localidad=dir_localidad,
                    dir_provincia=dir_provincia,
                    dir_cp = order.dir_cp,
                    dir_obs = order.dir_obs,
                    dir_correo= order.dir_correo,
                    order_total = order.order_total,
                    envio = 0,
                    status = "New",
                    is_ordered=True,
                    ip = request.META.get('REMOTE_ADDR'),
                    total_peso=0
                        ) 
                Order_New.save()
                messages.success(request,"Pedido guardado con exito.")

              
        return redirect('panel_pedidos_detalle',  str(order_number))  

def panel_productos_variantes(request):
    
    if validar_permisos(request,'PRODUCTO'):

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
    else:
        return render (request,"panel/login.html")

def panel_productos_del(request,product_id):
    
    if validar_permisos(request,'PRODUCTO'):

      
            producto = Product.objects.get(id=product_id)
            if producto:
                vari = Variation.objects.filter(product=producto)
                if vari:
                    vari.delete()
                producto.delete()
            
            return redirect('panel_catalogo') 
    else:
        return render (request,"panel/login.html")

def panel_producto_import_del_all(request):

    if validar_permisos(request,'PRODUCTO'):

      
            producto = Product.objects.filter()
            for product in producto:
                if product:
                    vari = Variation.objects.filter(product=product)
                    if vari:
                        vari.delete()
                    print("Eliminando", product)
                    product.delete()

            
            return redirect('panel_catalogo') 
    else:
        return render (request,"panel/login.html")

def panel_productos_variantes_del(request):
    
    if validar_permisos(request,'PRODUCTO'):

        if request.method =="POST":

            var_id = request.POST.get("var_id")
            product_id = request.POST.get("product_id")
            print("panel_productos_variantes_del")
            print(var_id)
            
            vari = Variation.objects.filter(id=var_id)

            if vari:
                vari.delete()
            
            return redirect('panel_producto_detalle', str(product_id)) 
    else:
        return render (request,"panel/login.html")

def panel_product_crud(request):
    
    if validar_permisos(request,'PRODUCTO'):

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
            
            
            
            access_token = request.POST.get("access_token")
            product_name = request.POST.get("product_name")
            description = request.POST.get("description")
            habilitado = request.POST.getlist("is_available[]")
            price = request.POST.get("price")
            images = request.POST.get("images")
            stock = request.POST.get("stock")
            cat_id = request.POST.get("category")
            subcat_id = request.POST.get("subcategory")
            is_popular = request.POST.getlist("is_popular[]")
            peso = request.POST.get("peso")
            
            peso = peso.replace(",", ".")
            stock = stock.replace(",", ".") 
            price = price.replace(",", ".") 

            category = Category.objects.get(id=cat_id)
            subcategory = SubCategory.objects.get(id=subcat_id)
            print("subcat_id",subcat_id)
            if product_id:
                producto = Product.objects.filter(id=product_id).first()
                created_date = producto.created_date
                
                if not images:
                    images = "none.jpg" #default      
                else:
                    images = producto.images
                
                if habilitado:
                    habilitado=True
                else:
                    habilitado=False

                if is_popular:
                    popular = True
                else:
                    popular = False

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
                        subcategory = subcategory,
                        created_date =created_date, 
                        modified_date=datetime.today(),
                        is_popular=popular,
                        peso=peso
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
                        subcategory = subcategory,
                        created_date= datetime.today(),
                        modified_date=datetime.today(),
                        peso=peso,
                        )
                if producto:
                    producto.save()
                    product_id = producto.id

            return redirect('panel_catalogo')
    else:
        return render (request,"panel/login.html")

def panel_producto_img(request):

    if validar_permisos(request,'PRODUCTO'):          
        if request.method =="POST":
            product_id = request.POST.get("product_id")

            try:
                if request.POST.get("imgFile"):
                    fileitem = request.POST.get("imgFile")
                    
                #imgroot = "photos/products/none.jpg" #default
                # check if the file has been uploaded
                #if fileitem.name:
                #    # strip the leading path from the file name
                #    fn = os.path.basename(fileitem.name)
                #    # open read and write the file into the server
                #    open(f"media/photos/products/{fn}", 'wb').write( fileitem.file.read())  #"/media/photos/products/
                #    
                #    imgroot = f"photos/products/{fileitem}"
                if not fileitem:
                    fileitem = 'none.jpg'


                print(fileitem)

                if product_id:
                    producto = Product.objects.filter(id=product_id).first()
                    #UPDATE IMAGE
                    print("***  UPDATE IMAGE ***")
                    producto = Product(
                            id=product_id ,
                            images=fileitem,
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
    else:
        return render (request,"panel/login.html")

def panel_producto_habilitar(request,product_id=None,estado=None):

    if validar_permisos(request,'PRODUCTO'):    
          
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
    else:
        return render (request,"panel/login.html")

def panel_usuario_list(request):
    
    if validar_permisos(request,'PERMISOS'): 

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

    else:
        return render (request,"panel/login.html")

def panel_usuario_permisos(request,user_id=None):
    
    if validar_permisos(request,'PERMISOS'): 
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
    else:
        return render (request,"panel/login.html")

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
    if validar_permisos(request,'PERMISOS'): 
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
    else:
        return render (request,"panel/login.html")

def panel_usuario_permisos_actualizar(request,user_id=None,id_pk=None,codigo=None,tipo=None,valor=None):  #Tipo (Ver (1) / Modificar(2)) - Valor (True / False)
    #Carga los permisos no asignados al usuario para poder editarlos.
    if validar_permisos(request,'PERMISOS'): 
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
    else:
        return render (request,"panel/login.html")

def panel_cliente_list(request):
    
    if validar_permisos(request,'CLIENTE'):

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
    else:
        return render (request,"panel/login.html")

def panel_cliente_detalle(request,id_cliente=None):
    
    if validar_permisos(request,'CLIENTE'):

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
    else:
        return render (request,"panel/login.html")

def panel_registrar_pago(request,order_number=None):
    
    if validar_permisos(request,'PEDIDOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if order_number:
            orden = Order.objects.get(order_number=order_number)
            cuentas = Cuentas.objects.all()
            total = orden.order_total - orden.envio
        context = {
            'orden':orden,
            'cuentas':cuentas,
            'permisousuario':permisousuario,
            'total':total,
        
        }
        print(orden)
        return render(request,'panel/registrar_pago.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_enviar_datos_pago(request,order_number=None):

    if validar_permisos(request,'PEDIDOS'):

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
        return render(request,'panel/enviar_datos_pago.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_confirmar_pago(request,order_number=None):

    if validar_permisos(request,'PEDIDOS'):
       
        if request.method =="POST":
            # GRABAR TRX EN PAYMENT
            total = 0  #Subtotal items + costo envio
            subtotal=0  #Subtotal 
            envio=0
            quantity=0
            current_user = request.user

           
            envio = request.POST.get("envio")
            cuenta_id = request.POST.get("cuenta")

           
            envio = envio.replace(",", ".")
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
    else:
        return render (request,"panel/login.html")

def panel_movimientos_list(request):
    
    if validar_permisos(request,'MOVIMIENTOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        print("panel_movimientos_list")
        fecha_1=None
        fecha_2=None
        if request.method =="POST":
          
            fecha_1 = request.POST.get("fecha_desde")
            fecha_2 = request.POST.get("fecha_hasta")     
        
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=15) 
            fecha_desde = fecha_hasta - dias
        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')

        mov = Movimientos.objects.filter(fecha__range=[fecha_desde,fecha_hasta])
        #cuentas = Cuentas.objects.all()
        print("fecha_desde",fecha_desde)
        print("Fecha_hasta",fecha_hasta)

        context = {
            'mov':mov,
            'permisousuario':permisousuario,
        #    'cuentas':cuentas,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta,
                       
        }
        
        return render(request,'panel/lista_movimientos.html',context) 

    else:
        return render (request,"panel/login.html")

def panel_transferencias_list(request):
    
    if validar_permisos(request,'TRANSFERENCIAS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        transf = Transferencias.objects.filter()
        cuentas = Cuentas.objects.all()
        
        context = {
            'transf':transf,
            'permisousuario':permisousuario,
            'cuentas':cuentas,
                       
        }
        
        return render(request,'panel/lista_transferencias.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_cierre_registrar(request):
    
    if validar_permisos(request,'CIERRE CONTABLE'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        mes = 0
        anio=0
        cuenta=0

        if request.method =="POST":
            mes = request.POST.get("mes")
            anio = request.POST.get("anio")
           

        if mes==0 and anio==0:
            #***************************************
            # POR DEFAULT TOMAMOS EL MES CORRIENTE
            yr = int(datetime.today().strftime('%Y'))
            dt = 1
            mt = int(datetime.today().strftime('%m'))
            fecha_desde = datetime(yr,mt,dt)
        else:
            yr = int(anio)
            mt = int(monthToNum(mes))
            dt = 1
            fecha_desde = datetime(yr,mt,dt)
        

        sel_mes =  NumTomonth(mt)
        sel_anio = yr
        if mt==12:
            mt=1
            yr+=1
        else:    
            mt = int(mt) + 1

        fecha_hasta = datetime(yr,mt,dt)
        fecha_hasta = fecha_hasta + timedelta(days=-1)
        
        if cuenta==0:
            cuenta = 1

       
        meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        anios = [yr-1, yr,yr+1]
      
        print(yr, fecha_desde,fecha_hasta)


        totales_ingresos_ventas = Movimientos.objects.filter(idcierre__isnull=True,ordernumber__isnull=False,movimiento=1,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')

        totales_ingresos_varios = Movimientos.objects.filter(idcierre__isnull=True,ordernumber__isnull=True,movimiento=1,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')


        totales_ingresos = Movimientos.objects.filter(idcierre__isnull=True,movimiento=1,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')
    
    
        totales_egresos = Movimientos.objects.filter(idcierre__isnull=True,movimiento=2,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')


        totales_resultado = Movimientos.objects.filter(idcierre__isnull=True,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')
      
     
        context = {
            'permisousuario':permisousuario,
            'totales_egresos':totales_egresos,      
            'totales_ingresos_ventas':totales_ingresos_ventas,  
            'totales_ingresos_varios':totales_ingresos_varios, 
            'totales_ingresos':totales_ingresos,
            'totales_resultado':totales_resultado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'meses':meses,
            'anios':anios,
            'sel_mes': sel_mes,
            'sel_anio':sel_anio,

                       
        }
        
        return render(request,'panel/registrar_cierre.html',context) 

    else:
        return render (request,"panel/login.html")

def panel_importar_productos(request):
    
    if validar_permisos(request,'IMPORTAR PRODUCTOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
        context = {
            'permisousuario':permisousuario,
            'modelo':2,
                       
        }
        
        return render(request,'panel/importar_productos.html',context) 
    else:
        return render (request,"panel/login.html")

def export_xls(request,modelo=None):
    #MODELO:
    #1 - Movimientos 
    #2 - Pedidos
    #3 - Productos
    #4 - Pedidos Temp 

        print("Export to Excel")
        response = HttpResponse(content_type='application/ms-excel')
        if modelo==1:
            response['Content-Disposition']='attachment; filename=Movimientos'+ str(datetime.now()) + '.xls'
        elif modelo==2:
            response['Content-Disposition']='attachment; filename=Pedidos_'+ str(datetime.now()) + '.xls'
        elif modelo==3:
            response['Content-Disposition']='attachment; filename=Articulos_'+ str(datetime.now()) + '.xls'
        elif modelo==4:
            response['Content-Disposition']='attachment; filename=Pedidos_Temp_'+ str(datetime.now()) + '.xls'
        else:
            response['Content-Disposition']='attachment; filename=Export_'+ str(datetime.now()) + '.xls'
        
        wb = xlwt.Workbook(encoding='utf-8')


        if validar_permisos(request,'EXPORTAR MOVIMIENTOS'):    
            if modelo==1: #MOVIMIENTOS

                sheet = "balance"
                ws = wb.add_sheet(sheet)
                if request.method =="POST":
                    fecha_desde = request.POST.get("fechadesde")
                    fecha_hasta = request.POST.get("fechahasta")
            
                if not fecha_desde or not fecha_hasta:
                    fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
                    dias = timedelta(days=356) 
                    fecha_desde = fecha_hasta - dias
                else:
                
                    fecha_desde = datetime.strptime(fecha_desde, '%d/%m/%Y')
                    fecha_hasta = datetime.strptime(fecha_hasta, '%d/%m/%Y')

                
                row_num=0
                font_style= xlwt.Style.XFStyle()
                font_style.font.bold = True
                columns = ['Fecha','Cliente','Movimiento','Cuenta','Monto','observaciones','Nro de Transferencia','Nro de Pedido']
                for col_num in range(len(columns)):
                    ws.write(row_num,col_num,columns[col_num],font_style)
                font_style = xlwt.Style.XFStyle()
                rows = Movimientos.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values_list(
                    'fecha','cliente','movimiento__movimiento','cuenta__nombre','monto','observaciones','idtransferencia','ordernumber__order_number')
                for row in rows:
                    row_num += 1
                    for col_num in range(len(row)):
                        if col_num==4:
                            monto = float("{0:.2f}".format((float)(row[4])))
                            #ws.write(row_num,col_num,'$ '+str('{0:,}'.format(int(round(monto)))))
                            ws.write(row_num,col_num,int(round(monto)))
                        else:
                            ws.write(row_num,col_num, str(row[col_num]),font_style)
                wb.save(response)

                return response
        else:
             return render (request,"panel/login.html")
        if validar_permisos(request,'EXPORTAR PEDIDOS'):
            if modelo==2: #PEDIDOS
                count_status=3

                if request.method =="POST":
                    fecha_desde = request.POST.get("fechadesde")
                    fecha_hasta = request.POST.get("fechahasta")
               
                if not fecha_desde or not fecha_hasta:
                    fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
                    dias = timedelta(days=30) 
                    fecha_desde = fecha_hasta - dias
                else:
                
                    fecha_desde = datetime.strptime(fecha_desde, '%d/%m/%Y')
                    fecha_hasta = datetime.strptime(fecha_hasta, '%d/%m/%Y')

                #print(fecha_desde,fecha_hasta)
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
                    columns = ['Pedido','Fecha','Total','Nombre','Apellido','email','Producto','Cantidad','Precio']
                    for col_num in range(len(columns)):
                        ws.write(row_num,col_num,columns[col_num],font_style)
                    font_style = xlwt.Style.XFStyle()

                    items_pedidos = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta],status=sheet)
                    rows = OrderProduct.objects.filter(order__in=items_pedidos).values_list('order__order_number','order__fecha','order__order_total','order__email','order__first_name','order__last_name','product__product_name','quantity','product_price')
     
                    for row in rows:
                        row_num += 1      
                        for col_num in range(len(row)):              
                            if col_num==7 or col_num==8 or col_num==2:
                                monto = float("{0:.2f}".format((float)(row[col_num])))
                                ws.write(row_num,col_num,int(round(monto)))
                            else:
                                ws.write(row_num,col_num, str(row[col_num]),font_style)
                wb.save(response)
                return response
        else:
            return render (request,"panel/login.html")

        if validar_permisos(request,'EXPORTAR PRODUCTOS'):
            if modelo==3: #PRODCUTOS

                sheet = "productos"

                ws = wb.add_sheet(sheet)
                row_num=0
                font_style= xlwt.Style.XFStyle()
                font_style.font.bold = True
                columns = ['Nombre','Description','Precio','images','stock','Habilitado','Category','Sub Category']
                for col_num in range(len(columns)):
                    ws.write(row_num,col_num,columns[col_num],font_style)
                font_style = xlwt.Style.XFStyle()

                rows = Product.objects.filter().values_list('product_name','description','price','images','stock','is_available','category__category_name','subcategory__subcategory_name').order_by('product_name')
                
                for row in rows:
                    row_num += 1      
                    for col_num in range(len(row)):              
                        if col_num==2 or col_num==4: #Numericos
                            monto = float("{0:.2f}".format((float)(row[col_num])))
                            ws.write(row_num,col_num,int(round(monto)))
                        else:
                            ws.write(row_num,col_num, str(row[col_num]),font_style)
                    
                wb.save(response)
                return response
        else:
            return render (request,"panel/login.html")

        if validar_permisos(request,'EXPORTAR PEDIDOS'):
            if modelo==4: #PEDIDOS  TEMP  (DE LA TABLA TEMPORAL)
                print("Export pedidos Temp")
                sheet = "Pedidos Temp"
                ws = wb.add_sheet(sheet)
                
                row_num=0
                font_style= xlwt.Style.XFStyle()
                font_style.font.bold = True
                columns = ['Mes','Fecha','Apellido','Nombre','Producto','Cantidad','Venta','Precio','Origen Operacion']
                for col_num in range(len(columns)):
                    ws.write(row_num,col_num,columns[col_num],font_style)
                font_style = xlwt.Style.XFStyle()

                items_pedidos = ImportTempOrders.objects.filter(usuario=request.user)
                rows = ImportTempOrdersDetail.objects.filter(codigo__in=items_pedidos).values_list('codigo__created_at','codigo__created_at','codigo__last_name','codigo__first_name','product','quantity','subtotal','subtotal','codigo__codigo')
     
                for row in rows:
                    row_num += 1      
                    for col_num in range(len(row)):
                        
                        if col_num==0:
                            format_string = '%Y-%m-%d %H:%M:%S'
                            str_mes = str(row[col_num])
                            str_mes = datetime.strptime(str_mes, format_string)
                            str_mes = str_mes.month
                            ws.write(row_num,col_num,str_mes,font_style)
                        elif col_num==5 or col_num==6 :
                            monto = float("{0:.2f}".format((float)(row[col_num])))
                            ws.write(row_num,col_num,int(round(monto)))
                        
                        elif col_num==7: #Calculo el precio
                            subtotal = float("{0:.2f}".format((float)(row[col_num])))
                            qty = float("{0:.2f}".format((float)(row[5])))
                            precio = subtotal/qty
                            ws.write(row_num,col_num,int(round(precio)))
                        else:
                            ws.write(row_num,col_num,str(row[col_num]),font_style)
                        
                        #elif col_num==6:
                        #    print(col_num,"--6>",row[col_num])
                        #    qty = int(row[col_num-2])
                        #    subtotal =  int(row[col_num-1])
                        #    precio = float("{0:.2f}".format((float)(subtotal/qty)))
                        #    ws.write(row_num,col_num, int(precio),font_style)
                        #    ws.write(row_num,col_num+1, str(row[col_num]),font_style)
                        #else:
                        #    print(col_num,"--else>",row[col_num])
                        #    ws.write(row_num,col_num,str(row[col_num]),font_style)

                wb.save(response)
                return response
        else:
            return render (request,"panel/login.html")
    
def import_productos_xls(request):

    if validar_permisos(request,'IMPORTAR PRODUCTOS'):
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
                        if sheet1.cell_value(rowNumber, 0).lower() != "producto":
                            product_id=0
                            product_name = sheet1.cell_value(rowNumber, 0)
                            tmp_producto = ImportTempProduct.objects.filter(product_name=product_name, usuario = request.user).first()
                            if not tmp_producto:
                                #Valido que exista la categoria
                                cat_name = sheet1.cell_value(rowNumber, 6)
                                sub_cat_name = sheet1.cell_value(rowNumber, 7)
                                img_name = sheet1.cell_value(rowNumber, 3)
                                if not img_name:
                                    img_name = 'none.jpg'

                                print("Articulo:",product_name,"| categoria:",cat_name,"| subCategoria",sub_cat_name)
                                slug_cat = slugify(cat_name).lower()
                                print("slug_cat",slug_cat)
                                cat = Category.objects.filter(slug=slug_cat)
                                if not cat:
                                    print("Crear Categoria:",cat_name)
                                    category = Category(
                                        category_name=cat_name ,
                                        slug = slugify(cat_name.lower()),
                                        description = cat_name,
                                        cat_image = 'none.jpg',
                                        orden = 99
                                    )
                                    category.save()
                                    print("Categoria Save")
                                
                                #SI NO EXISTEN LA CATEGORIA Y LA SUB CATEGORIA LAS CREO ANTES.
                                #AHORA BUSCO LAS CATEGORIAS Y LAS ASOCIO AL PRODUCTO
                                cat = Category.objects.get(slug=slug_cat)

                                slug_subcat = cat.slug +'-'+ sub_cat_name
                                slug_subcat = slugify(slug_subcat).lower()

                                sub_cat = SubCategory.objects.filter(category=cat,sub_category_slug=slug_subcat).first()
                                if cat:
                                    print("Tengo cat",cat.id)
                                    if not sub_cat:
                                        print("No teng subcat",slug_cat)
                                       
                                        sub_cat = SubCategory(
                                            category=cat,
                                            subcategory_name=sub_cat_name.strip(),
                                            sub_category_slug=slug_subcat,
                                            sub_category_description=""
                                            )
                                        sub_cat.save()
                                        print("sub Categoria .Save:",slug_subcat)
                                        sub_cat = SubCategory.objects.get(category=cat,subcategory_name=sub_cat_name)
                                    if sub_cat:
                                        print("Peso:",sheet1.cell_value(rowNumber, 8))
                                        tmp_producto = ImportTempProduct(
                                            product_name=product_name,
                                            slug=slugify(product_name).lower(),
                                            description= sheet1.cell_value(rowNumber, 1),
                                            variation_category = "", #sheet1.cell_value(rowNumber, 2),
                                            variation_value = "", #sheet1.cell_value(rowNumber, 3),
                                            price=sheet1.cell_value(rowNumber, 2),
                                            images=img_name,
                                            stock=sheet1.cell_value(rowNumber, 4),
                                            is_available=sheet1.cell_value(rowNumber, 5),
                                            category=cat.category_name, #  sheet1.cell_value(rowNumber, 8),
                                            subcategory=sub_cat.subcategory_name,# sheet1.cell_value(rowNumber, 9),
                                            created_date= datetime.today(),
                                            modified_date=datetime.today(),
                                            usuario = request.user,
                                            peso = int(sheet1.cell_value(rowNumber, 8))
                                            #is_popular = False,
                                                )
                                        tmp_producto.save()
                                        if tmp_producto:
                                            product_id = tmp_producto.id
                                            cant_ok=cant_ok+1
                                        else:
                                            cant_error=cant_error+1
                                            error_str = error_str + "Error al grabar el registro ROW: " + str(rowNumber)
                                    else:
                                        error_str = error_str + "Categoría / SubCategoria inexistente " + cat_name + " ROW: " + str(rowNumber)
                                        cant_error=cant_error+1
                                else:
                                    print("Categoria no encontrada:", cat_name)
                                    error_str = error_str + " (CATEGORIA NO ENCONTRADA:" + cat_name + ") "
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
                        error_str= error_str + product_name + "(category:" + cat_name + ")"
                        error_str= error_str + f" - Unexpected {err=}, {type(err)=}"
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
    else:
            return render (request,"panel/login.html")

def import_precios(request):

    print("IMPORTAR PRECIOS")
    if validar_permisos(request,'IMPORTAR PRECIOS'):
        cant_ok = 0
        cant_error =0
        error_str=""

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if request.method=="POST":
            try:
                myfile = request.FILES['rootfile']
                if myfile:
                    #fs = FileSystemStorage()
                    #filename = fs.save(myfile.name,myfile)
                    #archivo = fs.url(filename)
            
                    #int_fin = len(archivo)
                    #archivo = archivo[1:int_fin]
                    print("myFile", myfile )
                    fn = os.path.basename(myfile.name)
                    # open read and write the file into the server
                    open(f"media/{fn}", 'wb').write(myfile.file.read())
                    archivo = f"media/{myfile}"
                    #archivo = f"{myfile}"

            except:
                archivo=""
           
            if archivo:
            
                print("Archivo", archivo )
                workbook = xlrd.open_workbook(archivo)
                print("Abriendo arhcivo...")

                
                #Get the first sheet in the workbook by index
                sheet1 = workbook.sheet_by_index(0)

                #Get each row in the sheet as a list and print the list
                for rowNumber in range(sheet1.nrows):
                    try:
                        row = sheet1.row_values(rowNumber)
                        if sheet1.cell_value(rowNumber, 0) != "producto": # Saco la primera file
                            producto = sheet1.cell_value(rowNumber, 0)
                            precio = sheet1.cell_value(rowNumber, 1)

                            print(producto,precio)
                            try:
                                print(precio)
                                precio = float(precio)
                                print(precio)
                            except ValueError:
                                cant_error += 1
                                error_str+="<br> El precio del articulo "+ str(producto)+" no es valido."
                                pass

                            tmp_producto = Product.objects.get(product_name=producto)
                            if tmp_producto:
                                    tmp_producto = Product(
                                        id=tmp_producto.id,
                                        product_name=producto,
                                        slug=tmp_producto.slug,
                                        description=tmp_producto.description,
                                        price=precio,
                                        images=tmp_producto.images,
                                        stock=tmp_producto.stock,
                                        is_available=tmp_producto.is_available,
                                        category=tmp_producto.category,
                                        subcategory=tmp_producto.subcategory,
                                        created_date=tmp_producto.created_date,
                                        modified_date=datetime.today() ,
                                        is_popular = False, 
                                        peso = tmp_producto.peso,                                      
                                            )
                                    tmp_producto.save()
                                    if tmp_producto:
                                        product_id = tmp_producto.id
                                        cant_ok=cant_ok+1
                                    else:
                                        cant_error=cant_error+1
                                        error_str = error_str + "<br> Error al grabar el articulo: " + str(producto)
                                    
                        
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
                        error_str= error_str + producto
                        error_str= error_str + f" - Unexpected {err=}, {type(err)=}"
                        cant_error=cant_error+1
                        
                #Borro el archivo
                os.remove(archivo)
                
        context = {
                    'cant_ok':cant_ok,
                    'permisousuario':permisousuario,
                    'cant_error':cant_error,
                    'error_str':error_str,
                   
                            
                    }
        return render(request,'panel/importar_precios.html',context)
    else:
            return render (request,"panel/login.html")

def import_stock(request):

    print("IMPORTAR STOCK")
    if validar_permisos(request,'IMPORTAR STOCK'):
        cant_ok = 0
        cant_error =0
        error_str=""

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if request.method=="POST":
            try:
                myfile = request.FILES['rootfile']
                if myfile:
                    #fs = FileSystemStorage()
                    #filename = fs.save(myfile.name,myfile)
                    #archivo = fs.url(filename)
            
                    #int_fin = len(archivo)
                    #archivo = archivo[1:int_fin]
                    print("myFile", myfile )
                    fn = os.path.basename(myfile.name)
                    # open read and write the file into the server
                    open(f"media/{fn}", 'wb').write(myfile.file.read())
                    archivo = f"media/{myfile}"
                    #archivo = f"{myfile}"

            except:
                archivo=""
           
            if archivo:
            
                print("Archivo", archivo )
                workbook = xlrd.open_workbook(archivo)
                print("Abriendo arhcivo...")

                
                #Get the first sheet in the workbook by index
                sheet1 = workbook.sheet_by_index(0)

                #Get each row in the sheet as a list and print the list
                for rowNumber in range(sheet1.nrows):
                    try:
                        row = sheet1.row_values(rowNumber)
                        if sheet1.cell_value(rowNumber, 0) != "producto": # Saco la primera file
                            producto = sheet1.cell_value(rowNumber, 0)
                            stock = sheet1.cell_value(rowNumber, 1)

                            print(producto,stock)
                            try:
                               stock = int(stock)
                                
                            except ValueError:
                                cant_error += 1
                                error_str+="<br> El stock del articulo "+ str(producto)+" no es valido."
                                pass

                            tmp_producto = Product.objects.get(product_name=producto)
                            if tmp_producto:
                                    estado = tmp_producto.is_available
                                    if stock < 1:
                                        estado = False

                                    tmp_producto = Product(
                                        id=tmp_producto.id,
                                        product_name=producto,
                                        slug=tmp_producto.slug,
                                        description=tmp_producto.description,
                                        price=tmp_producto.price,
                                        images=tmp_producto.images,
                                        stock=stock,
                                        is_available=estado,
                                        category=tmp_producto.category,
                                        subcategory=tmp_producto.subcategory,
                                        created_date=tmp_producto.created_date,
                                        modified_date=datetime.today(),
                                        is_popular = False,   
                                        peso = tmp_producto.peso,                                     
                                            )
                                    tmp_producto.save()
                                    if tmp_producto:
                                        product_id = tmp_producto.id
                                        cant_ok=cant_ok+1
                                    else:
                                        cant_error=cant_error+1
                                        error_str = error_str + "<br> Error al grabar el articulo: " + str(producto)
                                    
                        
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
                        error_str= error_str + producto
                        error_str= error_str + f" - Unexpected {err=}, {type(err)=}"
                        cant_error=cant_error+1
                        
                #Borro el archivo
                os.remove(archivo)
                
        context = {
                    'cant_ok':cant_ok,
                    'permisousuario':permisousuario,
                    'cant_error':cant_error,
                    'error_str':error_str,
                   
                            
                    }
        return render(request,'panel/importar_stock.html',context)
    else:
            return render (request,"panel/login.html")

def guardar_tmp_productos(request): 
   
    articulos_tmp = ImportTempProduct.objects.filter(usuario=request.user)

    if articulos_tmp:
        for a in articulos_tmp:
            try:
                producto = Product.objects.filter(product_name=a.product_name)
                category = Category.objects.get(category_name=a.category)
                print(category)
                if not producto:
                    if not a.images:
                      imagen = "photos/products/none.jpg" #default      
                    else:
                        imagen = a.images

                    producto = Product(
                        product_name = a.product_name,
                        slug=slugify(a.product_name).lower(),
                        description = a.description,
                        category = category,
                        subcategory = SubCategory.objects.get(category=category,subcategory_name=a.subcategory),
                        images = imagen,
                        stock = a.stock,
                        price = float(a.price),
                        is_available = a.is_available,
                        created_date= datetime.today(),
                        modified_date=datetime.today(),
                        peso = a.peso, 
                    )
                    producto.save()
            except ObjectDoesNotExist:
                print ("articulo ya existente ", a.product_name )
                
            except Exception as err:
                print(a.product_name, f"guardar_tmp_productos {err=}, {type(err)=}")


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
    
    if validar_permisos(request,'IMPORTAR PRODUCTOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
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
    else:
            return render (request,"panel/login.html")

def panel_categoria_list(request):
    
    if validar_permisos(request,'CATEGORIA'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        categoria = Category.objects.filter().all()
        context = {
            'categoria':categoria,
            'permisousuario':permisousuario,
           
        }
       
        return render(request,'panel/lista_categorias.html',context) 
    else:
            return render (request,"panel/login.html")

def panel_categoria_del(request,id_categoria=None):
    
    if validar_permisos(request,'CATEGORIA'):


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
    else:
            return render (request,"panel/login.html")

def panel_subcategoria_detalle(request,id_subcategoria=None):

    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    print("Pasaron por acaaaaaaaaaaaaa")
    if validar_permisos(request,'SUBCATEGORIA'):
        if request.method =="GET":
            if id_subcategoria:
                subcategoria = SubCategory.objects.get(id=id_subcategoria)
                categoria = Category.objects.get(id=subcategoria.category.id)
            else:
                subcategoria =[]
                categoria=[]

            print(categoria)
            context = {
                'subcategoria':subcategoria,
                'categoria':categoria,
                'permisousuario':permisousuario,
                   }
         
            return render(request,'panel/subcategoria.html' ,context)

    
    else:
        return render (request,"panel/login.html")

def panel_subcategoria_save(request,id_categoria=None,id_subcategoria=None):

    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    
    print("panel_subcategoria_save")
    print("categoria:",id_categoria)
    print("subcategoria:",id_subcategoria)

    if validar_permisos(request,'SUBCATEGORIA'):
        if request.method =="GET":
            if id_categoria:
                categoria = Category.objects.get(id=id_categoria)
            else:
                categoria=[]
                
            if id_subcategoria:
                subcategoria = SubCategory.objects.get(id=id_subcategoria)
            else:
                subcategoria =[]

            context = {
                'subcategoria':subcategoria,
                'categoria':categoria,
                'permisousuario':permisousuario,
                   }
        
            return render(request,'panel/subcategoria.html',context)

        if request.method =="POST":
            
            nombre = request.POST['nombre']
            description = request.POST['description']
            idsubcategoria = request.POST['id_subcategoria']
            idcategoria = request.POST['id_categoria']
            orden = request.POST['orden']

            if idsubcategoria:
                subcategoria = SubCategory.objects.get(id=idsubcategoria)
                categoria = Category.objects.get(id=subcategoria.category.id)
                if subcategoria:
                    slug_subcategoria = categoria.category_name
                    slug_subcategoria = slug_subcategoria.lower() + " " + nombre.lower() #El espacio lo saca en slugify

                 

                    subcategoria = SubCategory(
                        id=idsubcategoria,
                        category=categoria,
                        subcategory_name  = nombre,
                        sub_category_slug = slugify(slug_subcategoria),
                        sub_category_description = description,
                        orden=orden
                        )
                    subcategoria.save()
                    messages.success(request, f'SubCategoria actualizada con exito!')

                    subcategoria = SubCategory.objects.filter(category=categoria)
            else:
                    categoria = Category.objects.get(id=idcategoria)
                    slug_subcategoria = categoria.category_name
                    slug_subcategoria = slug_subcategoria.lower() + " " + nombre.lower() #El espacio lo saca en slugify


                    subcategoria = SubCategory(
                        category=categoria,
                        subcategory_name  = nombre,
                        sub_category_slug = slugify(slug_subcategoria),
                        sub_category_description = description,
                        orden=orden
                        )
                    subcategoria.save()
                    messages.success(request, f'SubCategoria creada con exito!')

                    subcategoria = SubCategory.objects.filter(category=categoria)
            
            context = {
                'categoria':categoria,
                'subcategoria':subcategoria,
                'permisousuario':permisousuario,
                       }

            return render(request,'panel/categoria_detalle.html',context) 

    else:
        return render (request,"panel/login.html")

def panel_subcategoria_del(request,id_subcategoria=None):
        
    if validar_permisos(request,'SUBCATEGORIA'):

        if id_subcategoria:
            subcategoria = SubCategory.objects.filter(id=id_subcategoria).first()

            if subcategoria:
                id_categoria = subcategoria.category.id
                print("id_categoria",id_categoria)
                subcategoria.delete()

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categoria = Category.objects.get(id=id_categoria)
        subcategoria = SubCategory.objects.filter(category=categoria)

        context = {
            'categoria':categoria,
            'subcategoria':subcategoria,
            'permisousuario':permisousuario,
           
        }
       
        return render(request,'panel/categoria_detalle.html',context) 

    else:
            return render (request,"panel/login.html")
            
def panel_categoria_detalle(request,categoria_id=None):
    
    if validar_permisos(request,'CATEGORIA'):

        print("panel_categoria_detalle")
        print("********************************")

        if request.method =="GET":

            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            if categoria_id:
                categoria = Category.objects.get(id=categoria_id)
                subcategoria = SubCategory.objects.filter(category=categoria)
            else:
                categoria=[]
                subcategoria =[]

            context = {
                'categoria':categoria,
                'subcategoria':subcategoria,
                'permisousuario':permisousuario,
           
                }
       
            return render(request,'panel/categoria_detalle.html',context) 

        if request.method =="POST":
            cat_id = request.POST.get("categoria_id")
            cat_nombre = request.POST.get("category_name")
            cat_descripcion = request.POST.get("description")
            cat_imagen = request.POST.get("images")
            cat_orden = request.POST.get("orden")
            

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
                else:
                    cat_imagen = "photos/categories/none.jpg"        
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
                        slug = slugify(cat_nombre.lower()),
                        description = cat_descripcion,
                        cat_image = cat_imagen,
                        orden = cat_orden,
                    )
                    category.save()
            else:
                category = Category(
                    category_name=cat_nombre ,
                    slug = slugify(cat_nombre.lower()),
                    description = cat_descripcion,
                    cat_image = cat_imagen,
                    orden = cat_orden,
                )
                category.save()
            categoria = Category.objects.filter().all()         
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
            context = {
                'categoria':categoria,
                'permisousuario':permisousuario,
            
            }
        
            return render(request,'panel/lista_categorias.html',context) 
    else:
            return render (request,"panel/login.html")

def import_pedidos_xls(request):

    if validar_permisos(request,'IMPORTAR PEDIDOS'):
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
                                    bcorreo = True
                                else:
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
                                #print("Datos adicionales....",codigo)
                                
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
                                        usuario        = request.user,
                                        status          = False
                                        )                                    
                                    new_pedido.save()
                                
                                    if new_pedido:       
                                        #LINEAS DE ARTICULOS
                                        #print(mensaje)                                
                                        if "?pedido=" in mensaje:
                                            i_start_ped = mensaje.find('?pedido=')
                                            i_end_ped = mensaje.find('*',i_start_ped)
                                            codigo_ped = mensaje[i_start_ped + 8 :i_end_ped]
                                            #print("Codigo Detalle",codigo_ped,codigo)
                                        
                                        if codigo == codigo_ped:
                                            #Recorro artiuclos
                                            if "*Pedido:*" in mensaje:
                                                #print("i_start_ped",i_start_ped)
                                                i_start_ped = mensaje.find('*Pedido:*')
                                                
                                                #Arranca linea 
                                                mensaje = mensaje[i_start_ped+9:len(mensaje)]
                                                i_start_ped = mensaje.find('* x *') -3
                                                i=1
                                                i_fin_linea=0
                                                total_items=0
                                                
                                            #print("**************************")
                                            while i_end_ped > 0:
                                                i_start_ped= 1
                                                # BUSCO EL SIGNO PESOS PARA BUSCAR DESDE AHI EL PRIMER ASTERISCO DE LA CANTIDAD
                                                i_end_ped = mensaje.find('$',1) #Busco proxima linea para ver el final de esta
                                                i_end_ped = mensaje.find('*',i_end_ped) #Busco proxima linea para ver el final de esta
                                                i_end_ped = i_end_ped -1  # Esto es lo fijo buscado *
                                                linea = mensaje[i_start_ped:i_end_ped]
                                                linea = linea.lstrip() #Quito espacio a izquirda

                                                #print("-->", linea)
                                                # ** CANTIDAD **
                                                i_fin_linea = linea.find('*',1)
                                                quantity = linea[1:i_fin_linea]
                                                #print("quantity:",quantity)
                                                

                                                # ** PRODUCTO **
                                                i_ini_linea = i_fin_linea
                                                # Busco donde empieza el producto
                                                i_fin_linea = linea.find('* x *',i_ini_linea)
                                                i_fin_linea = i_fin_linea +  5
                                                i_ini_linea = i_fin_linea
                                                #Busco donde temina el producto
                                                i_fin_linea = linea.find('*',i_fin_linea)
                                                product = linea[i_ini_linea:i_fin_linea]  #.strip().replace('\r','').replace('\n')
                                                #print("Producto ", product)
                                                

                                                # ** PRECIOS **
                                                i_ini_linea = i_fin_linea
                                                i_ini_linea = linea.find('$',i_ini_linea)
                                                if linea.find('Cant. Artículos',i_ini_linea)>0:
                                                    i_fin_linea =  linea.find('Cant. Artículos',i_ini_linea)-1
                                                    subtotal = linea[i_ini_linea+1:i_fin_linea]
                                                    i_end_ped=0
                                                else:
                                                    subtotal = linea[i_ini_linea+1:len(linea)]
                                                subtotal = subtotal.replace(".","")

                                                #print("Producto ", product, "Qty", quantity, "Precio",subtotal)    
                                                try:
                                                        codigo = codigo
                                                    
                                                        new_linea_pedido = ImportTempOrdersDetail(
                                                            codigo = new_pedido,
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


                                               
                                                mensaje = mensaje[i_end_ped:len(mensaje)]
                                            #print("**************************")
                                    else:
                                        print("Pedido no grabado",codigo)

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

        total_pedido=0
        pedidos_total = ImportTempOrders.objects.filter(usuario = request.user).aggregate(Sum('order_total'))
        total_pedido=pedidos_total["order_total__sum"]
            
        
            

        
        cant_ok = pedidos_tmp.count()
        print("total_pedido",total_pedido)
        context = {
                    'cant_ok':cant_ok,
                    'permisousuario':permisousuario,
                    'cant_error':cant_error,
                    'error_str':error_str,
                    'pedidos_tmp':pedidos_tmp,
                    'articulos_tmp':articulos_tmp,
                    'total_pedido':total_pedido,                
                    }
        return render(request,'panel/importar_pedidos.html',context)
    else:
            return render (request,"panel/login.html")

def validar_tmp_pedidos(request):
    
    #print("validar_tmp_pedidos")

    pedidos_tmp = ImportTempOrders.objects.filter(usuario=request.user)
    if pedidos_tmp:
        
        for enc in pedidos_tmp:
            order_total = 0
            status_enc = True
            #print("Temp pedidos Create", enc.updated_at)
            pedidos_det_tmp = ImportTempOrdersDetail.objects.filter(usuario=request.user,codigo=enc.id)
            if pedidos_det_tmp:
                for a in pedidos_det_tmp:
                    try:
                        slug=slugify(a.product).lower()
                        #print("sulg prod:",slug)
                        producto = Product.objects.filter(slug=slug).first()
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
                            detalle_pedido.save()
                        else:
                            status_enc = False

                        #AUNQUE NO EXISTA EL PRODUCTO VALIDO LOS TOTALES PARA EL EXPORT A EXCEL (QUEDA EN ROJO)
                        order_total = order_total + a.subtotal
                            

                    except Exception as err:
                        #print("Error no controlado: ", a.product)
                        #print(f"Unexpected {err=}, {type(err)=}")
                        pass
                print("total 1", order_total, "total 2",enc.order_total)
                if order_total != enc.order_total:
                    status_enc = False


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
                order_total = order_total,
                status = status_enc 
            ) 
            #print("encabezado updated_at:", encabezado.updated_at)
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
    
    if validar_permisos(request,'PEDIDOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if order_number:
            orden = Order.objects.get(order_number=order_number)
        context = {
            'orden':orden,
            'permisousuario':permisousuario,
        
           }
        print(orden)
        return render(request,'panel/registrar_entrega.html',context) 
    else:
            return render (request,"panel/login.html")

def panel_confirmar_entrega(request):
    
    if validar_permisos(request,'PEDIDOS'):

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
    else:
            return render (request,"panel/login.html")

def panel_pedidos_eliminar_pago(request,order_number=None):
    
    if validar_permisos(request,'PEDIDOS'):
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
                        ordenes.payment = pago
                        ordenes.status="New"
                        ordenes.nro_tracking=""
                        ordenes.fecha_tracking=None
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
    else:
            return render (request,"panel/login.html")

def panel_pedidos_eliminar_entrega(request,order_number=None):
    
    if validar_permisos(request,'PEDIDOS'):

        print(">>>>Eliminar Entrega: ",order_number)
        try:
            if order_number:
                print("--->", order_number)
                ordenes = Order.objects.get(order_number=order_number)
                if ordenes:
                    id_ordenes = ordenes.id
                    ordenes.id = ordenes.id
                    ordenes.status = "Cobrado"
                    ordenes.nro_tracking=""
                    ordenes.fecha_tracking=None
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
    else:
            return render (request,"panel/login.html")

def panel_movimientos_transf(request,idtrans=None):
    
    if validar_permisos(request,'TRANSFERENCIAS'):

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


            monto_origen=monto_origen.replace(",",".")
            monto_origen=monto_origen.replace("-","")
            monto_destino=monto_destino.replace(",",".")
            monto_destino=monto_destino.replace("-","")
            conversion=conversion.replace(",",".")
            
            
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
    else:
            return render (request,"panel/login.html")

def registrar_movimiento(request,idmov=None):
        
    if validar_permisos(request,'MOVIMIENTOS'):
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
    else:
            return render (request,"panel/login.html")

def panel_transferencias_eliminar(request,idtrans=None):
    
    if validar_permisos(request,'TRANSFERENCIAS'):

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
    else:
            return render (request,"panel/login.html")

def panel_movimiento_eliminar(request,idmov=None):
        
    if validar_permisos(request,'MOVIMIENTOS'):
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
    else:
            return render (request,"panel/login.html")

def panel_pedidos_modificar(request,order_number=None,item=None,quantity=None):
    
    if validar_permisos(request,'PEDIDOS EDIT'):

            print("Order:",order_number)
            print("product_name",item)
            print("Quantity", quantity)

            if quantity == 0:
                print("Error quantity")
                messages.error(request, "La cantidad no puede ser cero.")
                return redirect('pedidos/detalle/edit/' + order_number)


            producto = Product.objects.filter(pk=item).first()
            if producto:
                print("Modificar Pedido: ",order_number)
                product_price = producto.price
                
                try:
                    if order_number:
                        print("--->", order_number)
                        pedido = Order.objects.get(order_number=order_number)
                        if pedido:
                            id_pedido = pedido.id
                            #Si existe elimino el registro
                            existe = OrderProduct.objects.filter(order_id=id_pedido,product=producto).exists()
                            if existe:
                                articulos = OrderProduct.objects.filter(order_id=id_pedido).first()
                                articulos = OrderProduct (
                                    id = articulos.id,
                                    order = pedido,
                                    user = request.user,
                                    product = producto,
                                    quantity = articulos.quantity + float(quantity),
                                    product_price = product_price,
                                    updated_at =  datetime.today(),
                                    created_at = articulos.created_at
                                )
                                articulos.save()
                            else:    
                                #articulos = OrderProduct.objects.filter(order_id=id_pedido).values()
                                articulos = OrderProduct (
                                    order = pedido,
                                    user = request.user,
                                    product = producto,
                                    quantity = quantity,
                                    product_price = product_price,
                                    updated_at =  datetime.today()
                                )
                                articulos.save()
                            print("Recalcular Totales")
                            panel_recalcular_totales(order_number)

                            messages.error(request,"Articulo ingresado ",'green')          
                            return redirect('/panel/pedidos/detalle/edit/' + order_number)                 
                    else:
                        print("No se encontro el Nro de Orden")        
                    return redirect('/panel/pedidos/detalle/edit/' + order_number)
                except Exception as err:
                    error_str=  f"panel_pedidos_modificar {err=}, {type(err)=}"
                    messages.error(request,"Error Exception:" + error_str,'red')
                    return redirect('panel_pedidos','New')
    else:
            return render (request,"panel/login.html")

def panel_recalcular_totales(order_number=None):

    print("panel_recalcular_totales",order_number)
    subtotal = 0
    pedido = Order.objects.get(order_number=order_number)
    if pedido:
        pesoarticulos=0
        id_pedido = pedido.id
        print("order_number",order_number)
        order_product = OrderProduct.objects.filter(order=id_pedido)
        print("items",order_product)
        if order_product:
            for i in order_product:
                subtotal += i.product_price * i.quantity
                #Recalculo el pese de los productos
                product = Product.objects.get(id=i.product_id)
                pesoarticulos += product.peso * i.quantity 
                

            pedido = Order(
                pk = id_pedido,
                order_number = order_number,
                order_total = subtotal,
                created_at = pedido.created_at,
                envio= pedido.envio,
                fecha = pedido.fecha,
                user = pedido.user,
                payment = pedido.payment, 
                
                first_name = pedido.first_name, 
                last_name  =pedido.last_name, 
                email  = pedido.email,
                dir_telefono  = pedido.dir_telefono,
                dir_calle  = pedido.dir_calle,
                dir_nro  = pedido.dir_nro,
                dir_localidad  = pedido.dir_localidad,
                dir_provincia  = pedido.dir_provincia,
                dir_cp  = pedido.dir_cp,
                dir_obs  = pedido.dir_obs,
                dir_correo  = pedido.dir_correo,
                order_note  = pedido.order_note,
           
                status = "New",
                ip  = pedido.ip,
                is_ordered  = pedido.is_ordered,
                updated_at  = datetime.today(),
                total_peso = pesoarticulos

            )
            pedido.save()

def panel_pedidos_obtener_linea(request,item=None):
    
    if validar_permisos(request,'PEDIDOS EDIT'):


        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        item_line = OrderProduct.objects.filter(id=item).first()
        if item_line:
            precio = item_line.product_price
            quantity = float(item_line.quantity)
            item_subtotal = float(item_line.product_price) * float(item_line.quantity)
            product = item_line.product.id
            order_number = item_line.order.order_number

            producto = Product.objects.filter(pk=product).first()
            if producto:
                nombre_producto = producto.product_name

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

   
        print("order_number",order_number)
        print("item",product)
        print("quantity",quantity)
        print("item_subtotal",item_subtotal)
        print("precio",precio)
        print("nombre_producto",nombre_producto)

        context = {
            'edit_order_number':order_number,
            'edit_item':item_line,
            'edit_quantity':quantity,
            'edit_item_subtotal': item_subtotal,
            'edit_precio':precio,
            'edit_product_name':nombre_producto,
            'edit_item_id':item,
            'ordenes':ordenes,
            'permisousuario':permisousuario,
            'ordenes_detalle':ordenes_detalle,
            'subtotal': subtotal,
            'pago_pendiente': pago_pendiente,
            'entrega_pendinete':entrega_pendinete,
            'entregado':entregado        
             }
        return render(request,'panel/pedido_detalle_edit.html',context) 
            
    else:
            return render (request,"panel/login.html")

def panel_reporte_articulos(request):

    if validar_permisos(request,'REPORTE ARTICULOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        context = {
            'permisousuario':permisousuario
             }
        return render(request,'panel/reporte_articulos.html',context) 
            
    else:
            return render (request,"panel/login.html")