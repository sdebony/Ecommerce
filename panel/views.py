#Control K + Control 0 Expande y contrae el codigo
#Control K + Control J

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect,HttpResponse
from django.urls import reverse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from accounts.models import AccountPermition,Permition
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from store.models import Product,Variation,Costo,ProductKit, ProductKitEnc,ReglaDescuento
from orders.models import Order, OrderProduct,Payment,OrderShipping,OrigenVenta,OrderProductKitItem
from category.models import Category, SubCategory #,Orden_picking
from accounts.models import Account, UserProfile    
from .models import Alerta
from contabilidad.models import Cuentas, Movimientos,Operaciones, Transferencias,CierreMes,ConfiguracionParametros
from panel.models import ImportTempProduct, ImportTempOrders, ImportTempOrdersDetail,ImportDolar
from compras.models import CompraDolar,ProveedorArticulos,ComprasDet,ComprasEnc
from accounts.forms import UserForm, UserProfileForm
from meli.models import meli_params
from django.db.models.functions import TruncMonth
from django.db.models.functions import Round
from django.db import transaction
from slugify import slugify
from datetime import timedelta,datetime,timezone
from decimal import Decimal
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from django.db.models import Sum, Avg, F, Q

import requests
from django.db.models import Case, When, Value, FloatField, ExpressionWrapper, F
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery
from django.db.models import Sum, F, Q, Count, DecimalField
from django.db.models.functions import TruncDate
from time import sleep  # Simular un proceso largo
from carts.models import CartItem
from django.http import JsonResponse

from collections import defaultdict


from .utils import consultar_costo_envio,consultar_sucursal_bycp,oca_consultar_costo_envio_by_cart,ca_consultar_costo_envio_by_cart  # Asegúrate de que esta función esté disponible

import json
import calendar

import locale

# Configurar la localización a español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

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
import itertools
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

# Función para generar un slug único
def generate_unique_slug(product_slug, product_id=None):
    new_slug = slugify(product_slug).lower()
    # Verificar si el slug ya existe
    unique_slug = new_slug
    for i in itertools.count(1):
        # Filtra por slug y omite el producto que estamos actualizando (por su ID)
        if not Product.objects.filter(slug=unique_slug).exclude(id=product_id).exists():
            break
        # Si ya existe, genera un nuevo slug con un sufijo numérico
        unique_slug = f"{new_slug}-{i}"
    return unique_slug

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

def panel_buscar_productos(request):
    query = request.GET.get('q', '')  # Obtener término de búsqueda
    productos = Product.objects.filter(product_name__icontains=query)[:20]  # Limitar resultados a 20
    data = [{"id": prod.id, "product_name": prod.product_name} for prod in productos]
    return JsonResponse(data, safe=False)

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

def panel_verificar_alertas(request):


    #Alerta de inventario
    # Obtener los productos con stock <= stock_minimo y disponibles
    productos_bajo_stock = Product.objects.filter(stock__lte=F('stock_minimo'), is_available=True)
    for producto in productos_bajo_stock:
       
        titulo="Alerta Inventario"
        mensaje="Producto: " + str(producto.product_name) + " Stock Actual: " + str(producto.stock) + " Stock Mínimo: " + str(producto.stock_minimo)
        mensaje_startswith="Producto: " + str(producto.product_name) + " Stock Actual: "
        if not Alerta.objects.filter(titulo=titulo, mensaje__startswith=mensaje_startswith).exists():
            Alerta.objects.create(usuario=request.user,  # Usuario actual
                titulo=titulo,
                mensaje=mensaje
                )
    return True

def panel_home(request):

    
    if validar_permisos(request,'PANEL'):

        if settings.ACTIVAR_ALERTAS == 'SI':
            panel_verificar_alertas(request)
            alertas = Alerta.objects.filter(usuario=request.user, leido=False)
            cant_alertas = alertas.count()
        else:
            alertas = []
            cant_alertas = 0

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
              
        context = {
            'permisousuario':permisousuario,
            'alertas': alertas,
            'cant_alertas':cant_alertas
            }
        print("Acceso Panel Home")

        return render (request,"panel/base.html",context)
    else:
        return render (request,"panel/login.html")

def dashboard_ventas(request):
   # VENTAS DEL DIAS

    if validar_permisos(request,'DASHBOARD VENTAS'):
        
        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")     
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=1) 
            fecha_desde = fecha_hasta - dias
        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        pedidos_totales = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).aggregate(
            cantidad=Count('order_number'),total=Sum('order_total')
            )
      
        pedidos_list = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta])
      
        cuenta = Cuentas.objects.all()


        
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
            'pedidos_totales':pedidos_totales,
            'pedidos_list':pedidos_list,
            'cuenta':cuenta,
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
        if mt == 13:
            mt = 1
            yr=yr+1

       

        lim_fecha_hasta = datetime(yr,mt,dt)
        lim_fecha_hasta = lim_fecha_hasta + timedelta(days=-1)

        if not fecha_1 and not fecha_2 :
            fecha_desde = lim_fecha_desde
            fecha_hasta = lim_fecha_hasta

        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')


        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
                
        current_month = timezone.now().month
        current_year = timezone.now().year

        cuentas = Cuentas.objects.filter(
            moneda__simbolo='$' , limite__gte=1 # Filtro por el símbolo de la moneda
        ).annotate(
            total_monto=Coalesce(
                Subquery(
                    Movimientos.objects.filter(
                        cuenta=OuterRef('pk'),
                        movimiento__codigo = 'ING',
                        fecha__month=current_month,
                        fecha__year=current_year
                    ).values('cuenta').annotate(total_monto=Sum('monto')).values('total_monto')[:1]
                ), 
                Value(0),
                output_field=FloatField()  # Especifica el tipo de campo como FloatField
            ),
            total_order_total=Coalesce(
                Subquery(
                    Order.objects.filter(
                        cuenta=OuterRef('pk'),
                        fecha__month=current_month,
                        fecha__year=current_year,
                        status='New'
                    ).values('cuenta').annotate(total_order_total=Sum('order_total')).values('total_order_total')[:1]
                ), 
                Value(0),
                output_field=FloatField()  # Especifica el tipo de campo como FloatField
            ),
            resta_monto=ExpressionWrapper(
                F('limite') - Coalesce(F('total_monto'), Value(0, output_field=FloatField())) - Coalesce(F('total_order_total'), Value(0, output_field=FloatField())),
                output_field=FloatField()  # Especifica el tipo de campo como FloatField
            )
        )

        #*******************************************
        # SOLICITUD DE COMPRA DE DOLARES
        #*********************************************
        
        resultado = []
       

        solicitudes = CompraDolar.objects.filter(estado=False)
        if solicitudes:
            for item in solicitudes:
                total_monto = 0
                total_acum_usd = 0
                total_acum_usd=0
                total_asig_usd=0
                #Obtengo los totales por fecha de los movimientos a partir de la fecha de solicitud
                fecha_solicitud = datetime.strptime(str(item.fecha), '%Y-%m-%d %H:%M:%S')
                fecha_solicitud = fecha_solicitud.strftime('%Y-%m-%d')
                cuenta_id = item.cuenta.id

                # **************************************
                # C O B R A D O 
                # **************************************
                # Consulta original para agrupar y sumar montos
                movimientos_agrupados = (
                    Movimientos.objects
                    .filter(fecha__gte=fecha_solicitud, movimiento=1, idcierre=0, cuenta_id=cuenta_id)
                    .values('fecha')
                    .annotate(total_monto=Sum('monto'))
                    .order_by('fecha')
                )
                # Inicializamos la variable para la suma total
                
                # Recorremos los resultados agrupados
                for item_mov in movimientos_agrupados:
                    fecha = item_mov['fecha']
                    total_monto = item_mov['total_monto']

                    # Obtener el promedio de ImportDolar para la fecha actual
                    import_dolar = ImportDolar.objects.filter(created_at__date=fecha).first()
                    promedio = import_dolar.promedio if import_dolar else None

                    # Si tenemos un valor de promedio, calcular y sumar
                    if promedio:
                        division_result = total_monto / promedio
                        division_result_redondeado = round(division_result, 2)
                        total_acum_usd += round(division_result_redondeado,2)

                total_monto_pesos =total_monto
                total_monto = 0
                # **************************************
                # A S I G N A D O -   N O  C O B R A D O 
                # ************************************** 
                pedidos_agrupados = (
                    Order.objects
                    .filter(status='New', cuenta=cuenta_id) #Para lo solicitado no toma la fecha ya que puede demorarse en pagar  #,fecha__gte=fecha_solicitud
                    .values('fecha')
                    .annotate(total_monto=Sum('order_total'))
                    .order_by('fecha')
                )
                # Inicializamos la variable para la suma total
                total_asig_usd = 0
                # Recorremos los pedidos agrupados x fecha
                for item_ped in pedidos_agrupados:
                    fecha = item_ped['fecha']
                    total_monto = item_ped['total_monto']

                    # Obtener el promedio de ImportDolar para la fecha actual
                    ped_import_dolar = ImportDolar.objects.filter(created_at__date=fecha).first()
                    ped_promedio = ped_import_dolar.promedio if ped_import_dolar else None

                    # Si tenemos un valor de promedio, calcular y sumar
                    if ped_promedio:
                        division_result = total_monto / ped_promedio
                        division_result_redondeado = round(division_result, 2)
                        total_asig_usd += round(division_result_redondeado,2)

                
                total_monto_pesos = total_monto_pesos + total_monto
                total_monto = 0
                
                 # Guardar los valores en un diccionario temporal
                resultado.append({
                    'solicitud': item,
                    'fecha':item.fecha,
                    'cuenta':item.cuenta.nombre,
                    'monto':item.monto,
                    'total_acum_pesos':round(total_monto_pesos,2),
                    'total_acum_usd': round(total_acum_usd,2),
                    'total_asig_usd': round(total_asig_usd,2),
                    'total_general_usd': round(total_acum_usd + total_asig_usd,2),
                    'faltan_usd': round(item.monto - total_acum_usd - total_asig_usd,2)
                })
            
        form = []
        context = {
            'permisousuario':permisousuario,
            'cuentas':cuentas,
            'resultado':resultado,
            'form': form,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta,
            'lim_fecha_desde':lim_fecha_desde,
            'lim_fecha_hasta':lim_fecha_hasta
           
            }
        print("Acceso Panel")
        
        return render (request,"panel/dashboard_cuentas.html",context)
    else:
        return render (request,"panel/login.html")

def dashboard_resultados(request,cuenta_id=None):

    if validar_permisos(request,'DASHBOARD RESULTADOS'):
        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")

        # POR DEFAULT TOMAMOS EL MES CORRIENTE
        yr = int(datetime.today().strftime('%Y'))
        dt = 1
        mt = int(datetime.today().strftime('%m'))
        lim_fecha_desde = datetime(yr,mt,dt)
 
        mt = int(mt) + 1
    
        if mt == 13:
            mt = 1
            yr=yr+1
        lim_fecha_hasta = datetime(yr,mt,dt)
        lim_fecha_hasta = lim_fecha_hasta + timedelta(days=-1)

        if not fecha_1 and not fecha_2 :
            fecha_desde = lim_fecha_desde
            fecha_hasta = lim_fecha_hasta

        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')


        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        # LE SACO LAS FECHAS PARA QUE TOME LOS SALDOS REALES ACTUALES
        #saldos = Movimientos.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('cuenta__nombre','cuenta__moneda').annotate(total=
        #    Round(Sum('monto'),output_field=DecimalField(max_digits=12, decimal_places=2)))
        saldos = Movimientos.objects.filter().values('cuenta__nombre','cuenta__moneda','cuenta__moneda__simbolo','cuenta__id').annotate(total=
            Round(Sum('monto'),output_field=DecimalField(max_digits=12, decimal_places=2))).filter(total__gt=0)

        if cuenta_id:
            mov = Movimientos.objects.filter(cuenta=cuenta_id).order_by('-fecha')
        else:
            print("none")
            mov=[]        

        context = {
            'permisousuario':permisousuario,
            'mov':mov,
            'saldos':saldos,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta
        }
        return render (request,"panel/dashboard.html",context)
    else:
        return render (request,"panel/login.html")  

def dashboard_control(request):

    if validar_permisos(request,'DASHBOARD CONTROL'):
        

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        resultados = Product.objects.aggregate(
            productos_stock_mayor_0=Count('id', filter=Q(stock__gt=0)),
            productos_stock_menor_igual_3=Count('id', filter=Q(stock__lt=F('stock_minimo')) & Q(is_available=True)),
            productos_disponibles=Count('id', filter=Q(is_available=True)),
            productos_costo_mayor_igual_precio=Count('id', filter=Q(costo_prod__gte=F('price'))),
            productos_activos_sin_costo = Count('id', filter=Q(costo_prod=0) & Q(is_available=True)),    #Costo = 0 y habilitado
            total_stock=Sum('stock', filter=Q(es_kit=False) & Q(is_available=True)),
            costo_stock=Sum(F('costo_prod') * F('stock'), filter=Q(es_kit=False) & Q(is_available=True))
        )

        # Accede a los valores usando las claves
        print("Stock Fisico:", resultados['total_stock'])
       
        # Filtrar los OrderProduct que pertenecen a órdenes con estado > 1
        total_facturacion=0
        orders_validas = Order.objects.exclude(status='New')        
        
        #TOTAL INGRESO REAL DE LO FACTURADO
        total_facturacion = Order.objects.exclude(status='New').aggregate(
            total_facturacion=Sum(
            F('order_total') 
            )
            )['total_facturacion']

        # Calcular la ganancia neta total excluyendo órdenes con status 'New'
        ganancia_total = (
            OrderProduct.objects.exclude(order__status='New')
            .annotate(
                ingreso_total=F('precio_unitario_cobrado') * F('quantity'),  # Ingresos totales por registro
                costo_total=F('costo') * F('quantity')  # Costos totales por registro
            )
            .aggregate(
                total_ingreso=Sum('ingreso_total'),  # Sumar todos los ingresos
                total_costo=Sum('costo_total')  # Sumar todos los costos
            )
        )

        # Calcular la ganancia neta
        ganancia_neta = ganancia_total['total_ingreso'] - ganancia_total['total_costo']
        print("Ganancia:", round(ganancia_neta,2))

        origenventa = OrigenVenta.objects.filter(codigo='MELI').first()
        total_facturacion_meli = Order.objects.filter(origen_venta=origenventa).exclude(status='New').aggregate(
            total_facturacion_meli=Sum(
            F('order_total') 
            )
            )['total_facturacion_meli']

        cant_ventas_meli = Order.objects.filter(origen_venta=origenventa).exclude(status='New').count()

        origenventa = OrigenVenta.objects.filter(codigo='WEB').first()
        total_facturacion_web = Order.objects.filter(origen_venta=origenventa).exclude(status='New').aggregate(
            total_facturacion_web=Sum(
            F('order_total') 
            )
            )['total_facturacion_web']

        cant_ventas_web = Order.objects.filter(origen_venta=origenventa).exclude(status='New').count()

        origenventa = OrigenVenta.objects.filter(codigo='TN').first()
        total_facturacion_tn = Order.objects.filter(origen_venta=origenventa).exclude(status='New').aggregate(
            total_facturacion_tn=Sum(
            F('order_total') 
            )
            )['total_facturacion_tn']

        cant_ventas_tn = Order.objects.filter(origen_venta=origenventa).exclude(status='New').count()


        # Obtener los márgenes
        margen_bruto = OrderProduct.objects.filter(order__in=orders_validas).aggregate(
            total_product_price=Sum(F('product_price')  * F('quantity')),  # Corrige las operaciones con F()
            total_product_cost=Sum(F('costo') * F('quantity'))
        )

        margen_utilidad = OrderProduct.objects.filter(order__in=orders_validas).aggregate(
            margen_utilidad_total=Sum(
                ((F('precio_unitario_cobrado')) * F('quantity')) - (F('costo') * F('quantity')),
                output_field=FloatField()  # Asegura que el resultado sea un campo flotante
            )
        )    
       
        

        total_product_price = margen_bruto['total_product_price']
        total_product_cost = margen_bruto['total_product_cost']
        total_ventas = orders_validas.count()
        total_articulos_vendidos = 0

        total_ganancia_real = round(float(total_facturacion) - float(total_product_cost),2)
        
   
        margen_bruto_total = None
        if total_product_cost:
            if  total_product_cost > 0:
                margen_bruto_total = round(((ganancia_neta / total_facturacion)) * 100, 2)  # Redondear a 2 decimales
            else:
                margen_bruto_total = None  # O manejarlo como prefieras si total_product_cost es 0

        multi_cuentas= settings.STORE_MULTI_CANAL
        total_ganancia_real = round(float(ganancia_neta),2)

        #STOCK TEORICO  LO COMPRADO MENOS LO VENDIDO
        # Sumar el total del campo cantidad del modelo ComprasDet
        compras_total = ComprasDet.objects.filter(id_compra_enc__estado=2).aggregate(total=Sum('cantidad'))['total'] or 0
     
        # Filtrar productos con es_kit=True
        productos_kit_total = OrderProduct.objects.filter(product__es_kit=True).annotate(
            unidades_totales=F('quantity') * F('product__productkitenc__cant_unidades')
        ).aggregate(total=Sum('unidades_totales'))['total'] or 0

   # Sumar el total de 'quantity' excluyendo los productos con 'product.es_kit = False'
        orders_total = OrderProduct.objects.filter(product__es_kit=False).aggregate(total=Sum('quantity'))['total'] or 0
       
        total_articulos_vendidos = int(productos_kit_total) + int(orders_total)
        # Generar el resultado en el formato requerido

        stock_control = int(compras_total) - int(total_articulos_vendidos)


        context = {
            'permisousuario':permisousuario,
            'resultados':resultados,
            'stock_control':stock_control,
            'margen_bruto_total':margen_bruto_total,
            'total_ganancia_real':total_ganancia_real,
            'total_articulos_vendidos':total_articulos_vendidos,
            'margen_utilidad':margen_utilidad,
            'total_facturacion_meli':total_facturacion_meli,
            'total_facturacion_web':total_facturacion_web,
            'total_facturacion_tn':total_facturacion_tn,
            'total_ventas':total_ventas,
            'cant_ventas_meli':cant_ventas_meli,
            'cant_ventas_web':cant_ventas_web,
            'cant_ventas_tn':cant_ventas_tn,
            'total_product_price':total_product_price,
            'total_facturacion':total_facturacion,
            'multi_cuentas':multi_cuentas,
                 }
        return render (request,"panel/dashboard_control.html",context)
    else:
        return render (request,"panel/login.html")  

def dashboard_resumen_ventas(request):

    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
    if validar_permisos(request,'DASHBOARD RESUMEN VENTAS'):
        
        # Obtener datos agregados con la relación origen_venta
        ventas_mensuales = Order.objects.filter(
            status__in=["Completed", "Cobrado", "Entregado"]
        ).annotate(
            mes=TruncMonth("fecha")
        ).values(
            "mes", "origen_venta__origen"  # Usar el campo 'origen' del modelo relacionado
        ).annotate(
            total=Sum("order_total")
        ).order_by("mes")

         # Calcular Ganancia Neta mensual usando los mismos parámetros que ventas_mensuales
        ganancias = (
            OrderProduct.objects.filter(order__status__in=["Completed", "Cobrado", "Entregado"])
            .annotate(
                mes=TruncMonth("order__fecha"),
                ingreso_total=F('precio_unitario_cobrado') * F('quantity'),  # Ingresos totales
                costo_total=F('costo') * F('quantity')  # Costos totales
            )
            .annotate(ganancia=F('ingreso_total') - F('costo_total'))  # Ganancia neta
            .values('mes')  # Agrupar por mes
            .annotate(total_ganancia=Sum('ganancia'))  # Ganancia acumulada por mes
            .order_by('mes')
        )

        # Convertir ganancias a un diccionario para fácil acceso
        ganancias_por_mes = {g['mes']: g['total_ganancia'] for g in ganancias}
        

        # Procesar datos
        datos_por_mes = defaultdict(lambda: {"Mercado Libre": 0, "Web": 0, "Tienda Nube":0, "Mercado Libre + Web + Tienda Nube": 0,"Ganancia Neta": 0 })
        for venta in ventas_mensuales:
            mes = venta["mes"]
            origen = venta["origen_venta__origen"]  # Usar el nombre del campo origen
            if origen in ["Mercado Libre", "Web", "Tienda Nube"]:
                print(origen)
                datos_por_mes[mes][origen] += venta["total"]
                datos_por_mes[mes]["Mercado Libre + Web + Tienda Nube"] += venta["total"]
            # Agregar ganancia neta del mes
            if mes in ganancias_por_mes:
                datos_por_mes[mes]["Ganancia Neta"] = ganancias_por_mes[mes]

        # Preparar listas
        meses = sorted(datos_por_mes.keys())
        ventas_mercado_libre = [datos_por_mes[mes]["Mercado Libre"] for mes in meses]
        ventas_web = [datos_por_mes[mes]["Web"] for mes in meses]
        ventas_tn = [datos_por_mes[mes]["Tienda Nube"] for mes in meses]
        ventas_combinadas = [datos_por_mes[mes]["Mercado Libre + Web + Tienda Nube"] for mes in meses]
        ganancias_netas = [datos_por_mes[mes]["Ganancia Neta"] for mes in meses]



        # Contexto para la plantilla
        context = {
            'labels': [mes.strftime("%b %Y") for mes in meses],  # Formato: Mes Año
            'ventas_mercado_libre': ventas_mercado_libre,
            'ventas_web': ventas_web,
            'ventas_tn': ventas_tn,
            'ventas_combinadas': ventas_combinadas,
            'ganancias_netas': ganancias_netas,  # Agregar la nueva lista
            'permisousuario':permisousuario,
        }
        
        return render(request, 'panel/dashboard_resumen_ventas.html', context) 
       
    else:
        return render (request,"panel/login.html")

def dashboard_ganancia_neta(request):
    # Obtener el año actual
    # Obtener el año actual

    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    
    if request.method =="POST":
        current_year = request.POST.get("anio")
    else:
        current_year = datetime.now().year


    yr = int(current_year)
    anios_disponibles = [yr-2,yr-1, yr,yr+1,yr+2]
        

    # Calcular Ganancia Neta mensual
    ganancias = (
        OrderProduct.objects.filter(order__fecha__year=current_year)
        .annotate(
            ingreso_total=F('precio_unitario_cobrado') * F('quantity'),  # Ingresos totales
            costo_total=F('costo') * F('quantity')  # Costos totales
        )
        .annotate(ganancia=F('ingreso_total') - F('costo_total'))  # Ganancia neta
        .values('order__fecha__month')
        .annotate(total_ganancia=Sum('ganancia'))  # Ganancia acumulada por mes
        .order_by('order__fecha__month')
    )

   
    # Calcular Gastos Mensuales
    gastos = (
        Movimientos.objects.filter(
            fecha__year=current_year,
            movimiento__codigo='EGR',  # Código de movimiento correspondiente a gastos
        )
        .exclude(id__in=ComprasEnc.objects.values('id_pago'))
        .values('fecha__month')
        .annotate(total_gasto=Sum('monto'))
        .order_by('fecha__month')
    )

    # Formatear datos para la tabla
    meses = list(range(1, 13))
    ganancias_data = {g['order__fecha__month']: g['total_ganancia'] for g in ganancias}
    gastos_data = {g['fecha__month']: g['total_gasto'] for g in gastos}

    # Asegurar valores por mes
    ganancias_list = [ganancias_data.get(m, 0) for m in meses]
    gastos_list = [gastos_data.get(m, 0) for m in meses]

    # Calcular diferencias considerando signos
    diferencias_list = [gan + gas for gan, gas in zip(ganancias_list, gastos_list)]
    
    # Preparar datos para la tabla
    tabla_datos = [
        {
            'mes': m,
            'ganancia': gan,
            'gasto': gas,
            'diferencia': dif
        }
        for m, gan, gas, dif in zip(meses, ganancias_list, gastos_list, diferencias_list)
    ]

    context = {
        'tabla_datos': tabla_datos,
        'permisousuario':permisousuario,
        'anio': current_year, 
        'anios_disponibles': anios_disponibles, 
    }

    return render(request, 'panel/dashboard_ganancia.html', context)

def panel_product_list_category(request):
    
    if validar_permisos(request,'PRODUCTO'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categorias = Category.objects.all()
        catalogo = Product.objects.all().order_by('-is_available','-stock','product_name')
        cantidad = catalogo.count()
        categoria=0
       
    
        if request.method =="GET":
            catalogo = Product.objects.all().order_by('-is_available','-stock','product_name')
            cantidad = catalogo.count()
    
        if request.method =="POST":
        
            category = request.POST.get("category")
            categoria=int(category)
           

            print("category",category)
         

            if category:
                if category=='0':
                    catalogo = Product.objects.all().order_by('-is_available','-stock','product_name')
                    cantidad = catalogo.count()
                else:
                    catalogo = Product.objects.filter(category=category).order_by('-is_available','-stock','product_name')
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
    
    print("Ducplicado panel_reporte_articulos. Linea: 259")
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
       

        catalogo = Product.objects.filter().all().order_by('-is_available','-stock','product_name')
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

        product_kit_det=[]
        producto = []
        variantes = []
        subcategoria=[]
        product_kit_enc=[]

        if product_id:
            product = get_object_or_404(Product, id=product_id)

            producto = Product.objects.get(product_name=product.product_name)
            categorias = Category.objects.all()
            variantes = Variation.objects.filter(product=product)
            subcategoria = SubCategory.objects.filter(category=producto.category).all()
           
            product_kit_enc = ProductKitEnc.objects.filter(productokit=product_id).first()
            if product_kit_enc:
                product_kit_det = ProductKit.objects.filter(productokit=product_kit_enc)

        else:
            categorias = Category.objects.all()
           
            

        try:
            print("panel_product_crud - habilitar_precios_externos")
            Permisos_pe = AccountPermition.objects.filter(user=request.user,codigo__codigo="PRECIOS EXTERNOS").first()
        
            if Permisos_pe:
                habilitar_precios_externos = 1
            else:
                habilitar_precios_externos = 0
        except ObjectDoesNotExist:
            habilitar_precios_externos = 0
            

        context = {
            'producto':producto,
            'product_kit_enc':product_kit_enc,
            'product_kit_det':product_kit_det,
            'permisousuario':permisousuario,
            'categorias': categorias,
            'subcategoria':subcategoria,
            'variantes':variantes,
            'precios_externos':habilitar_precios_externos,
        }
    
        return render(request,'panel/productos_detalle.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_list(request,status=None):
    
    if validar_permisos(request,'PEDIDOS'):
        if not status:
            status='New'

        dias_default_pedidos = settings.DIAS_DEFAULT_PEDIDOS  #Rango de fechas desde y hasta para filtros hoy - x dias

        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta") 

        

        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=dias_default_pedidos) 
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

        print(cantidad_new)

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

        #Permite cambiar canal de venta
        
        store_multi_canal = getattr(settings, 'STORE_MULTI_CANAL', False)
        if store_multi_canal==False:
            canal_venta="NO"
        else:
            canal_venta= settings.STORE_MULTI_CANAL.upper()
        
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
            "cuenta":cuenta,
            "canal_venta":canal_venta
             
            


        }
        return render(request,'panel/lista_pedidos.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_detalle(request,order_number=None):

    if validar_permisos(request,'PEDIDOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        resultado_final = []
        ordenes = Order.objects.get(order_number=order_number)
        ordenes_detalle = OrderProduct.objects.filter(order_id=ordenes.id).annotate(subtotal=
            Round(
                #Sum('product_price' - 'descuento_unitario')*Sum('quantity'),2
                Sum((F('product_price') - F('descuento_unitario')) * F('quantity')), 2
                ))

        subtotal=0
        subtotal_sin_desc=0
        for detalle in ordenes_detalle:
            subtotal = subtotal + detalle.subtotal  # Accede al subtotal de cada elemento
            subtotal_sin_desc = subtotal_sin_desc + round(float(detalle.quantity) * float(detalle.product_price),2)

        
            #Envio detalle de kits al order_recibe para el mail.
            kits = OrderProductKitItem.objects.filter(order_product=detalle).annotate(
                product_name=F('product__product_name')
                ).values('product_name', 'quantity','order_product')  # Selecciona solo el nombre del producto y la cantidad

            # Agregar al resultado final
            resultado_final.extend(list(kits))  # Convierte el queryset en lista y la extiende    

        
        idcuenta = ordenes.cuenta
        if idcuenta>0:
            cuenta = Cuentas.objects.get(id=idcuenta)
        else:
            cuenta= []

        
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

        store_multi_canal = getattr(settings, 'STORE_MULTI_CANAL', False)
        if store_multi_canal==False:
            canal_venta="NO"
        else:
            canal_venta= settings.STORE_MULTI_CANAL.upper()

        
        
        context = {
            'ordenes':ordenes,
            'permisousuario':permisousuario,
            'ordenes_detalle':ordenes_detalle,
            'products_and_quantities':resultado_final,
            'subtotal': subtotal,
            'subtotal_sin_desc':subtotal_sin_desc,
            'pago_pendiente': pago_pendiente,
            'entrega_pendinete':entrega_pendinete,
            'entregado':entregado,
            'cuenta':cuenta,
            "canal_venta":canal_venta
        }
        
        return render(request,'panel/pedidos_detalle.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_pedidos_imprimir_picking(request,order_number=None):

    if validar_permisos(request,'PEDIDOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        resultado_final=[]
        ordenes = Order.objects.get(order_number=order_number)
        ordenes_detalle = OrderProduct.objects.filter(order_id=ordenes.id)

        # Anotar los valores de orden_picking desde Category y SubCategory
        ordenes_detalle = ordenes_detalle.annotate(
            category_orden_picking=F('product__category__orden_picking'),
            subcategory_orden_picking=F('product__subcategory__orden_picking')
        )

        # Ordenar por Category.orden_picking primero y luego por SubCategory.orden_picking
        ordenes_detalle = ordenes_detalle.order_by('category_orden_picking', 'subcategory_orden_picking')

        # Ahora `ordenes_detalle` estará ordenado según el `orden_picking` de Category y SubCategory.

        #Envio detalle de kits al order_recibe para el mail.
        for detalle in ordenes_detalle:
            kits = OrderProductKitItem.objects.filter(order_product=detalle).annotate(
                product_name=F('product__product_name')
                ).values('product_name', 'quantity','order_product')  # Selecciona solo el nombre del producto y la cantidad

            # Agregar al resultado final
            resultado_final.extend(list(kits))  # Convierte el queryset en lista y la extiende    


                   
        context = {
            'ordenes':ordenes,
            'permisousuario':permisousuario,
            'ordenes_detalle':ordenes_detalle,
            'products_and_quantities':resultado_final
        }
        
        return render(request,'panel/pedido_picking.html',context) 
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
        archivo1="" 
        archivo2="" 
        archivo3=""     
        if request.method =="POST":
            print("Cargando imagen 1...")
            try:
                if request.FILES["imgFile1"]:
                    fileitem = request.FILES["imgFile1"]
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
            
            archivo1 = pdf_root
            
            print("Cargando imagen 2...")
            pdf_root=""
            try:
                if request.FILES["imgFile2"]:
                    fileitem = request.FILES["imgFile2"]
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

            archivo2 = pdf_root

            print("Cargando imagen 3...")
            pdf_root=""
            try:
                if request.FILES["imgFile3"]:
                    fileitem = request.FILES["imgFile3"]
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

            archivo3 = pdf_root
           
            
            if archivo1:  #Solo es requerido 1 archivo
                
                if pedido:

                    nro_tracking = request.POST.get("tracking")
                    #Guardar tracking
                    pedido.fecha_tracking = datetime.now()
                    pedido.nro_tracking = nro_tracking
                    pedido.save()

                    if  pedido.email:
                        mensaje = MIMEMultipart()
                        mensaje['From']=  settings.EMAIL_HOST_USER 
                        mensaje['To']=pedido.email 
                        mensaje['Subject']='Seguimiento del pedido ' + str(order_number)

                        mensaje.attach(MIMEText("Gracias por su compra.  Aqui le enviamos el seguimiento de su pedido junto con la foto del pedido. https://www.correoargentino.com.ar/formularios/e-commerce?id="+ str(nro_tracking),'plain'))
                        
                        archivo_adjunto1 = open('media/facturas/' + archivo1,'rb')
                        if archivo2:
                            archivo_adjunto2 = open('media/facturas/' + archivo2,'rb')

                        if archivo3:
                            archivo_adjunto3 = open('media/facturas/' + archivo3,'rb')

                        
                        if archivo1:
                            adjunto_MIME1 = MIMEBase('aplication','octet-stream')
                            adjunto_MIME1.set_payload((archivo_adjunto1).read())
                            encoders.encode_base64(adjunto_MIME1)

                            adjunto_MIME1.add_header('Content-Disposition',"attachment; filename= %s" %archivo1)
                            mensaje.attach(adjunto_MIME1)

                        if archivo2:
                            adjunto_MIME2 = MIMEBase('aplication','octet-stream')
                            adjunto_MIME2.set_payload((archivo_adjunto2).read())
                            encoders.encode_base64(adjunto_MIME2)

                            adjunto_MIME2.add_header('Content-Disposition',"attachment; filename= %s" %archivo2)
                            mensaje.attach(adjunto_MIME2)

                        if archivo3:
                            adjunto_MIME3 = MIMEBase('aplication','octet-stream')
                            adjunto_MIME3.set_payload((archivo_adjunto3).read())
                            encoders.encode_base64(adjunto_MIME3)

                            adjunto_MIME3.add_header('Content-Disposition',"attachment; filename= %s" %archivo3)
                            mensaje.attach(adjunto_MIME3)

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

            rs_cuenta = Cuentas.objects.get(id=cuenta)
            if rs_cuenta:
                cuenta_text = rs_cuenta.nombre 
                
         
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
                    dir_tipocorreo= pedido.dir_tipocorreo,
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
                        <td>Nombre: ''' + str(cuenta_text) + ''' </td>            
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
        print("panel_pedidos_detalle_edit")
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
        store_multi_canal = getattr(settings, 'STORE_MULTI_CANAL', False)
        if store_multi_canal==False:
            canal_venta="NO"
        else:
            canal_venta= settings.STORE_MULTI_CANAL.upper()

 

        context = {
            'ordenes':ordenes,
            'permisousuario':permisousuario,
            'ordenes_detalle':ordenes_detalle,
            'subtotal': subtotal,
            'pago_pendiente': pago_pendiente,
            'entrega_pendinete':entrega_pendinete,
            'entregado':entregado,
            "canal_venta":canal_venta
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
        print("panel_pedidos_eliminar:",order_number)
        if order_number:
                ordenes = Order.objects.get(order_number=order_number)
                if ordenes:
                    ordenes_detalle = OrderProduct.objects.filter(order_id=ordenes.id)
                    for linea in ordenes_detalle:
                        id_prd = linea.product.id
                        cantidad = linea.quantity
                        product = Product.objects.get(id=id_prd)
                        if product:
                            product.stock += float(cantidad)
                            product.save()

                   
                            if product.es_kit:
                                items_kits = OrderProductKitItem.objects.filter(order_product=linea.id)
                                if items_kits:
                                    for item_kit in items_kits:
                                    # Redusco Stock de los articulos Kits
                                  
                                        product = Product.objects.get(id=item_kit.product.id)
                                        if product:
                                            #pesoarticulos += product.peso * item.quantity 
                                            product.stock = product.stock + item_kit.quantity
                                            product.save()


                    if ordenes_detalle:
                        ordenes_detalle.delete()
                ordenes.delete()
                messages.success(request,"Pedido eliminado con exito.")
        
        return redirect('panel_pedidos','New')
    else:
        return render (request,"panel/login.html")

def panel_pedidos_del_detalle(request,order_number,id_linea):

    if validar_permisos(request,'PEDIDOS EDIT'):
        print("panel_pedidos_del_detalle")
        #articulo = Product.objects.filter(product_name=producto).first()
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.get(order_id=order.id,pk=id_linea)
    
        # Obtener todos los productos asociados a la orden
        productos_asociados = OrderProduct.objects.filter(order_id=order.id)
        print("Lineas de articulo del pedido:",str(productos_asociados.count()))

        # Verificar si es el último producto
        if productos_asociados.count() == 1:
            print("No se puede eliminar el ùltimo articulo. Elimine el pedido completo.")
            panel_recalcular_totales(order_number)
            messages.success(request,"No se puede eliminar el ùltimo articulo. Elimine el pedido completo.")
            return redirect('panel_pedidos_detalle',  str(order_number))    
        else:
            if ordered_products:
                cantidad = ordered_products.quantity  
                idprod = ordered_products.product.id         
                ordered_products = OrderProduct(
                    id = ordered_products.id,
                )        
                ordered_products.delete()
                #Agrego el stocl del producto borrado.
                product = Product.objects.get(id=idprod)
                if product:
                    product.stock += float(cantidad)
                    product.save()

                  
                    if product.es_kit:
                        items_kits = OrderProductKitItem.objects.filter(order_product=ordered_products)
                        if items_kits:
                            for item_kit in items_kits:
                            # Redusco Stock de los articulos Kits
                                print("Productos del KIT", item_kit.product.id,item_kit.product.product_name, item_kit.quantity)

                                product = Product.objects.get(id=item_kit.product.id)
                                if product:
                                    #pesoarticulos += product.peso * item.quantity 
                                    product.stock = product.stock + item_kit.quantity
                                    product.save()


                panel_recalcular_totales(order_number)
                messages.success(request,"Articulo eliminado con exito.")
                
        panel_pedidos_detalle(request,order_number)          
        return redirect('panel_pedidos_detalle',  str(order_number))  
    else:
        return render (request,"panel/login.html")
        
def panel_pedidos_save_detalle(request):

    if validar_permisos(request,'PEDIDOS EDIT'):

       
        if request.method =="POST":
            print("panel_pedidos_save_detalle")
            order_number = request.POST.get("edit_order_number")
            id_linea = request.POST.get("edit_item_id")
            cantidad = float(request.POST.get("edit_quantity"))
            precio = request.POST.get("edit_precio")
            descuento = request.POST.get("edit_descuento")

            

            if cantidad:
                if precio:
                    if order_number:
                        
                        order = Order.objects.get(order_number=order_number, is_ordered=True)
                        ordered_products = OrderProduct.objects.get(order_id=order.id,pk=id_linea)
                        if ordered_products:  
                            #Sumo Stock de linea eliminada
                            stock = ordered_products.quantity
                            producto = ordered_products.product_id
                           

                            product = Product.objects.get(id=producto)
                            if product:
                                saldo = product.stock
                                costo = product.costo_prod
                                ajuste_stock = float(saldo) + float(stock) - float(cantidad)
                                product.stock = ajuste_stock
                                product.save()

                            ordered_products = OrderProduct(
                                id = ordered_products.id,
                                quantity = cantidad,
                                product_price = precio,
                                order = ordered_products.order, 
                                payment = ordered_products.payment,
                                user =ordered_products.user,
                                product=ordered_products.product,
                                descuento_unitario = descuento,
                                precio_unitario_cobrado =float(precio) - float(descuento),    #Precio Unitario Cobrado sin impuestos ni comisiones
                                ordered=ordered_products.ordered,
                                created_at = ordered_products.created_at,
                                updated_at = datetime.today(),
                                costo = costo
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

def get_order_total(order_id):

    ordered_products = OrderProduct.objects.filter(order_id=order_id)
    total = sum([product.product_price * product.quantity for product in ordered_products])
    print("Total Enc:",total)
    return round(total, 2)  # Redondea el resultado a 2 decimales

def panel_pedidos_save_enc(request):

        print("panel_pedidos_save_enc")
        if request.method =="POST":
            
            order_number = request.POST.get("order_number")
            fecha = request.POST.get("fecha")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            dir_calle = request.POST.get("dir_calle")
            dir_nro = request.POST.get("dir_nro")
            dir_piso = request.POST.get("dir_piso")
            dir_depto = request.POST.get("dir_depto")
            dir_localidad = request.POST.get("dir_localidad")
            dir_provincia = request.POST.get("dir_provincia")
            dir_telefono = request.POST.get("dir_telefono")
            email = request.POST.get("email")
            order_total_comisiones = request.POST.get("enc_order_total_comisiones")
            order_total_impuestos = request.POST.get("enc_order_total_impuestos")
            order_total_descuentos = request.POST.get("enc_order_total_descuentos")
            envio = request.POST.get("enc_envio")
            origen_venta = request.POST.get("enc_origen_venta")

            print("origen_venta",origen_venta)
            origenventa = OrigenVenta.objects.filter(codigo=origen_venta).first()
            if not origenventa:
                canal_venta= settings.STORE_DEF_CANAL  #WEB
                origenventa = OrigenVenta.objects.filter(codigo=canal_venta).first()



            fecha = datetime.strptime(fecha, '%d/%m/%Y')
            
            order = Order.objects.get(order_number=order_number)
            if order:
                total = get_order_total(order.id)
                print("Total Order;",total)
                total = float(total) - float(order_total_comisiones) - float(order_total_impuestos) - float(order_total_descuentos) - float(envio)
                total = round(total,2)
                print("Nuevo total",total,order_total_comisiones,order_total_impuestos,order_total_descuentos,envio)

                Order_New = Order(
                    id = order.id,
                    order_number=order_number,
                    first_name=first_name,
                    last_name=last_name,
                    origen_venta = origenventa,
                    email=email,
                    created_at=order.created_at,
                    fecha=fecha,
                    updated_at=order.updated_at,
                    #user=user_account,
                    dir_telefono=dir_telefono,
                    dir_calle=dir_calle,
                    dir_nro =dir_nro,
                    dir_piso =dir_piso,
                    dir_depto =dir_depto,
                    dir_localidad=dir_localidad,
                    dir_provincia=dir_provincia,
                    dir_cp = order.dir_cp,
                    dir_obs = order.dir_obs,
                    dir_tipocorreo= order.dir_tipocorreo,
                    order_total_comisiones = order_total_comisiones,
                    order_total_impuestos = order_total_impuestos,
                    order_total_descuentos = order_total_descuentos,
                    order_total = round(total,2),
                    dir_correo= order.dir_correo,
                    dir_tipoenvio = order.dir_tipoenvio,
                    fecha_tracking = order.fecha_tracking, 
                    nro_tracking = order.nro_tracking,
                    envio = envio,
                    status = "New",
                    is_ordered=True,
                    ip = request.META.get('REMOTE_ADDR'),
                    total_peso=order.total_peso,
                    
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

def panel_crear_regla_descuento(request):

    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    categorias = Category.objects.all()  # Obtener todas las categorías
    productos = Product.objects.filter(is_available=True)


    if request.method == 'POST':
       
        print("Crear Reglas POST")
        nombre = request.POST.get('nombre')
        tipo_descuento = request.POST.get('tipo_descuento')
        valor = request.POST.get('valor')
        #categoria_id = request.POST.get('categoria')
        #subcategoria_id = request.POST.get('subcategoria')
        cantidad_minima = request.POST.get('cantidad_minima')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        activo = request.POST.get('activo') == 'on'

        monto_desde = request.POST.get('monto_desde') 
        monto_hasta = request.POST.get('monto_hasta') 
        acumulable = request.POST.get('acumulable') == 'off'

        productos = request.POST.get('productosSeleccionados', '')
        #categorias_ids = request.POST.getlist('categorias')  # Lista de IDs de categorías
        #subcategorias_ids = request.POST.getlist('subcategorias')  # Lista de IDs de subcategorías
        categorias = request.POST.getlist('categorias[]')
        subcategorias = request.POST.getlist('subcategorias[]')
        
        if productos:
            productos_lista = productos.split(',')
            productos = Product.objects.filter(id__in=productos_lista)
        
            print("productosSeleccionados:", productos_lista)  # Aquí deberías ver los IDs de los productos
        else:
            print("No se seleccionaron productos.")

        

        # Primero, crea la instancia de ReglaDescuento sin el campo `productos`
        regla_descuento = ReglaDescuento.objects.create(
            nombre=nombre,
            tipo_descuento=tipo_descuento,
            valor_descuento=valor if valor else 0,
            #categoria=categoria,
            #subcategoria=subcategoria,
            cantidad_minima=cantidad_minima if cantidad_minima else 0,
            monto_desde=monto_desde if monto_desde else 0,
            monto_hasta=monto_hasta if monto_hasta else 0,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=activo,
            acumulable=acumulable
        )
        # Luego, agrega los productos seleccionados a la relación ManyToMany
        regla_descuento.productos.add(*productos)  # Usar add() para agregar los productos seleccionados
        # Asociar categorías, subcategorías y productos
        if categorias:
            regla_descuento.categoria.clear()
            regla_descuento.categoria.add(*categorias)   
        if subcategorias:
            regla_descuento.subcategoria.clear()
            regla_descuento.subcategoria.add(*subcategorias)  

        regla_descuento.save()
        
        messages.success(request, 'Regla de descuento creada exitosamente.')
        return redirect('listar_reglas_descuento')

    context = {
        'permisousuario':permisousuario,
        'categorias':categorias,
        'productos':productos
    }
    
    return render(request, 'panel/producto_descuento_add.html',context)
    
def panel_editar_regla_descuento(request, pk):

    regla = get_object_or_404(ReglaDescuento, pk=pk)
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    categorias = Category.objects.all()  # Obtener todas las categorías
    productos = Product.objects.filter(is_available=True)
    regla_prod = regla.productos.all()
    categorias_con_subcategorias = []
    product=None
  
    for categoria in regla.categoria.all():
        subcategorias = regla.subcategoria.filter(category=categoria)
        if subcategorias.exists():
            for subcategoria in subcategorias:
                # Añadimos los ID y nombre como un par
                categorias_con_subcategorias.append({
                    'categoria_id': categoria.id,
                    'categoria_nombre': categoria.category_name,
                    'subcategoria_id': subcategoria.id,
                    'subcategoria_nombre': subcategoria.subcategory_name
                })
        else:
            # Añadimos solo la categoría si no tiene subcategoría
            categorias_con_subcategorias.append({
                'categoria_id': categoria.id,
                'categoria_nombre': categoria.category_name,
                'subcategoria_id': None,
                'subcategoria_nombre': None
            })



    if request.method == 'POST':

        monto_desde = request.POST.get('monto_desde')  if request.POST.get('monto_desde') else 0
        monto_hasta = request.POST.get('monto_hasta')  if request.POST.get('monto_hasta') else 0
        acumulable = request.POST.get('acumulable') 

        if acumulable=='on':
            acumulable = True
        else:
            acumulable = False

        
        categorias = request.POST.getlist('categorias[]')
        subcategorias = request.POST.getlist('subcategorias[]')
        productos_seleccionados = request.POST.get('productosSeleccionados','')
        
        print("productos_seleccionados",productos_seleccionados)
        
        if productos_seleccionados:
            producto_ids = productos_seleccionados.split(',')
            product = Product.objects.filter(id__in=producto_ids)

            print("product_list ----->>>>>>>>",producto_ids)

        
          

        regla.nombre = request.POST.get('nombre')
        regla.tipo_descuento = request.POST.get('tipo_descuento')
        regla.valor_descuento = request.POST.get('valor')
        regla.cantidad_minima = request.POST.get('cantidad_minima') if request.POST.get('cantidad_minima') else 0
        regla.fecha_inicio = request.POST.get('fecha_inicio')
        regla.fecha_fin = request.POST.get('fecha_fin')
        regla.activo = request.POST.get('activo') == 'on'
        regla.monto_desde = monto_desde
        regla.monto_hasta = monto_hasta
        regla.acumulable = acumulable

        if product:
            regla.productos.clear()
            regla.productos.add(*product)    
        if categorias:
            regla.categoria.clear()
            regla.categoria.add(*categorias)   
        if subcategorias:
            regla.subcategoria.clear()
            regla.subcategoria.add(*subcategorias)  

        regla.save()
        messages.success(request, 'Regla de descuento actualizada exitosamente.')
        return redirect('listar_reglas_descuento')
    
    
    context = {
        'regla': regla,
        'permisousuario':permisousuario,
        'categorias':categorias,
        'productos':productos,
        'regla_prod':regla_prod,
        'categorias_con_subcategorias':categorias_con_subcategorias
    }

    return render(request, 'panel/producto_descuento_add.html', context)

def panel_eliminar_regla_descuento(request, pk):
    regla = get_object_or_404(ReglaDescuento, pk=pk)

    if request.method == 'POST':
        regla.delete()
        messages.success(request, 'Regla de descuento eliminada exitosamente.')
        return redirect('listar_reglas_descuento')

    return render(request, 'panel/producto_descuento_del.html', {'regla': regla})

def panel_listar_reglas_descuento(request):
    reglas = ReglaDescuento.objects.all()
    categorias = Category.objects.all()  # Obtener todas las categorías
    subcategorias = SubCategory.objects.all()  # Obtener todas las subcategorías
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

    for regla in reglas:
        print(regla.fecha_inicio)

    
    context = {
        'categorias': categorias,
        'subcategorias': subcategorias,
        'reglas':reglas,
        'permisousuario':permisousuario
    }

    return render(request, 'panel/producto_descuento_list.html',context)

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

            print("panel_producto_import_del_all")
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
            habilitar_precios_externos=0

            try:
               
                precios_externos = AccountPermition.objects.filter(user=request.user,codigo__codigo="PRECIOS EXTERNOS").first()
            
                if precios_externos:
                    habilitar_precios_externos = 1
                else:
                    habilitar_precios_externos = 0
            except ObjectDoesNotExist:
                habilitar_precios_externos = 0

         

            context = {
                'producto':producto,
                'permisousuario':permisousuario,
                'categorias': categorias,
                'variantes':variantes,
                'precios_externos':habilitar_precios_externos, #1 Muestra para ingresar precios TN y ML
            }
        
            return render(request,'panel/productos_detalle.html',context) 

        if request.method =="POST":
            
            
            
            product_id = request.POST.get("product_id")
            product_name = request.POST.get("product_name").strip()
            description = request.POST.get("description", "").strip()
            habilitado = request.POST.getlist("is_available[]")
            price = request.POST.get("price")
            images = request.POST.get("images")
            stock = request.POST.get("stock")
            stock_minimo = request.POST.get("stock_minimo")
            cat_id = request.POST.get("category")
            subcat_id = request.POST.get("subcategory")
            is_popular = request.POST.getlist("is_popular[]")
            es_kit = request.POST.getlist("es_kit[]")
            peso = request.POST.get("peso")
            costo_prod = request.POST.get("costo_prod")
            ubicacion = request.POST.get("ubicacion").strip()
            
            try:
                stock_float = float(stock)
                stock_entero = int(stock_float)
            except ValueError:
                stock_entero = 0  # O cualquier valor por defecto
            
            if not costo_prod:
                costo_prod=0
            if not ubicacion:
                ubicacion=''
          
            if not stock_minimo:
                stock_minimo=0

            if not es_kit:
                es_kit = False
            else:
                es_kit = True

            category = Category.objects.get(id=cat_id)
            subcategory = SubCategory.objects.get(id=subcat_id)
            precio_tn = 0
            precio_ml = 0
            created_date = datetime.now()
            #print("subcat_id",subcat_id)
            if product_id:
                producto = Product.objects.filter(id=product_id).first()
                if producto:
                    created_date = producto.created_date
                    precio_tn =producto.precio_TN
                    precio_ml = producto.precio_ML

                    #print("producto",precio_tn,precio_ml,product_id)
                
                  
                if not images:
                    images = "none.jpg" #default      
                else:
                    images = images #producto.images
                
                if habilitado:
                    habilitado=True
                else:
                    habilitado=False

                if is_popular:
                    popular = True
                else:
                    popular = False
                
                if es_kit:
                    es_kit = True
                else:
                    es_kit = False

                product_slug = product_name.replace('ñ', 'enie')
                product_slug = product_name.replace('Ñ', 'eniee')
                print("product_slug: ",product_slug, "Product id", product_id)

                product_udp = Product.objects.get(id=product_id)
                
                if product_udp:
                    product_udp.product_name = product_name
                    product_udp.slug = product_udp.slug #generate_unique_slug(product_slug, product_id=product_udp.id)
                    product_udp.description = description
                    product_udp.price = price
                    product_udp.images = images
                    product_udp.imgfile = images
                    product_udp.stock = stock_entero
                    product_udp.stock_minimo = stock_minimo
                    product_udp.is_available = habilitado
                    product_udp.category = category
                    product_udp.subcategory = subcategory
                    product_udp.created_date = created_date
                    product_udp.modified_date = datetime.today()
                    product_udp.is_popular = popular
                    product_udp.peso = peso
                    product_udp.costo_prod = costo_prod
                    product_udp.ubicacion = ubicacion
                    product_udp.precio_ML = precio_ml
                    product_udp.precio_TN = precio_tn
                    product_udp.es_kit = es_kit

                    product_udp.save()
                    print("Save tabla Product")

                    #Actualizo la tabla KIT
                    if not es_kit:
                        producto_kit = ProductKit.objects.filter(productokit=product_id)
                        if producto_kit:
                            producto_kit.delete()
                            print("Delete tabla ProductKit")
                else:
                    print("Producto no encontrado")
            else:
                # ADD
                print("POS --> ADD")
                print(slugify(product_name))
                product_slug = product_name.replace('ñ', 'enie')
                product_slug = product_name.replace('Ñ', 'eniee')

                if not images:
                    images = "none.jpg" #default      

                if Product.objects.filter(slug=product_slug).exists():
                    print("Producto ya existe. Slug repetido")
                else:
                    producto = Product(
                            product_name=product_name,
                            slug=slugify(product_slug).lower(),
                            description= description,
                            price=price,
                            images=images,
                            imgfile = images,
                            stock=stock_entero,
                            stock_minimo = stock_minimo,
                            is_available=True,
                            category=category,
                            subcategory = subcategory,
                            created_date= datetime.today(),
                            modified_date=datetime.today(),
                            peso=peso,
                            costo_prod=costo_prod,
                            ubicacion=ubicacion,
                            precio_TN=precio_tn, # producto.precio_TN,
                            precio_ML=precio_ml, # producto.precio_ML
                            es_kit=es_kit
                            )
                    if producto:
                        producto.save()
                        product_id = producto.id

                    #Actualizo la tabla KIT
                    try:
                        producto_kit = ProductKit.objects.get(productokit=product_id)
                        if producto_kit:
                            producto_kit.delete()
                            print("Delete tabla ProductKit")
                    except ProductKit.DoesNotExist:
                        producto_kit = None  # O cualquier otra acción que prefieras

                    

            return redirect('panel_catalogo')
    else:
        return render (request,"panel/login.html")

def panel_product_kit(request,prod_id):
    
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    producto_kit = []
    producto_kit = get_object_or_404(Product, id=prod_id)
    
    if request.method == 'POST':
        #Save encabezado

        action = request.POST.get('action')

        if action == "save":
            producto_kit = get_object_or_404(Product, id=prod_id)
            cant_variedades = request.POST.get('cant_variedades')
            cant_unidades = request.POST.get('cant_unidades')

            
            ProductKitEnc.objects.update_or_create(
                productokit=producto_kit,
                defaults={
                    'cant_unidades': cant_unidades,
                    'cant_variedades': cant_variedades
                }
            )

            print("Kit grabado con éxito")   
            return redirect(reverse('panel_producto_detalle', kwargs={'product_id': prod_id}))        
    
    return render(request, 'panel/productos_kits.html', {'producto_kit': producto_kit, 'product_padre_id': prod_id, 'permisousuario': permisousuario})
    
def panel_buscar_producto_hijo(request):



    if 'term' in request.GET:
        term = request.GET.get('term')
       
        productos = Product.objects.filter(product_name__icontains=term)
        results = [{'id': prod.id, 'nombre': prod.product_name} for prod in productos]
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def panel_agregar_producto_al_kit(request):

    print("panel_agregar_producto_al_kit")
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
   
    if request.method == 'POST':
        
        product_padre_id = request.POST.get("product_padre_id")
        data = json.loads(request.POST.get('products', '[]'))
        # Procesar los productos seleccionados
        print(f'Productos recibidos: {data}')
       
        #Instancio al padre
        producto_kit = ProductKitEnc.objects.get(productokit=product_padre_id)

        # Filtrar y eliminar todos los registros relacionados en ProductKit
        ProductKit.objects.filter(productokit=producto_kit).delete()
    
        for producto in data:
            #Instancio al Hijo
            print("hijos:",producto)
            product = Product.objects.get(pk=producto)
            # Crear o actualizar cada registro
            ProductKit.objects.update_or_create(
                productokit=producto_kit,  # Clave primaria o criterio de coincidencia
                productohijo=product,      # Clave primaria o criterio de coincidencia
                defaults={}                # Campos adicionales para actualizar (si los hay)
            )
            
        print("Kit grabado con éxito")   
        # Suponiendo que tienes una consulta para obtener los permisos del usuario
        # Convertir el QuerySet en una lista de diccionarios
        return JsonResponse({'redirect_url': reverse('panel_producto_detalle', kwargs={'product_id': product_padre_id})})

  
       
    return redirect('panel_catalogo')

def panel_productos_kit_del(request,idkit):
    #El ID corresponde al ID DEL PRODUCTO DE LA TABLA PRODUCTKIT
    if validar_permisos(request,'PRODUCTO'):

        try:
            print("IDKIT: " ,idkit)

            producto_kit = ProductKit.objects.get(id=idkit)
            if producto_kit:
                id_prodPadre = producto_kit.productokit.productokit
                print("id_prodPadre",id_prodPadre.id)
                producto_kit.delete()
                print("Producto eliminado del kit.",id_prodPadre)
            return redirect(reverse('panel_producto_detalle', kwargs={'product_id': id_prodPadre.id}))
            
        except:
            print("Error: IDKIT: " ,idkit)
            return redirect('panel_catalogo') 
            
    else:
        return render (request,"panel/login.html")

def panel_producto_precio_ext(request):


    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        precio_tn = request.POST.get('precio_TN')
        precio_ml = request.POST.get('precio_ML')
        sku_meli = request.POST.get('sku_meli')
        url_meli = request.POST.get('url_meli')

        if not precio_tn:
            precio_tn=0
        if not precio_ml:
            precio_ml=0

        if not sku_meli:
            sku_meli=''
        else:
            sku_meli = sku_meli.strip() 
        if not url_meli:
            url_meli=''
        else:
            url_meli = url_meli.strip() 

        producto = Product.objects.get(id=product_id)
        if producto:
            producto.precio_TN = precio_tn
            producto.precio_ML = precio_ml
            producto.sku_meli = sku_meli
            producto.url_meli = url_meli
            producto.save()
    
    return redirect('panel_catalogo')

def panel_producto_img(request):

    if validar_permisos(request,'PRODUCTO'):          
        
        productos = Product.objects.all()
        for product in productos:
            product_id = product.id
            if product_id:
                imagen = str(product.images)
                #imagen = imagen.replace("%20"," ")

                #UPDATE IMAGE
                print(product_id,"***  UPDATE IMAGE ***",imagen)
                producto = Product(
                        id=product_id ,
                        images=imagen,
                        imgfile = imagen,
                        product_name=product.product_name,
                        slug=product.slug,
                        description=product.description,
                        price=product.price,
                        stock=product.stock,
                        peso=product.peso,
                        is_available=True,
                        category=product.category,
                        subcategory=product.subcategory,
                        created_date =product.created_date, 
                        modified_date=datetime.today(),
                        )
                producto.save()
                print("Producto actualizado: ",product_id)
            
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

                    # Actualiza el producto existente
                    producto.is_available = habilitado
                    producto.modified_date = datetime.today()
                    product_slug = producto.product_name.replace('ñ', 'enie')
                    product_slug = product_slug.replace('Ñ', 'eniee')
                    producto.slug = slugify(product_slug).lower()

                    # Guarda los cambios
                    producto.save()

                    
            except:
                print("Error: ", producto.product_name)
                

            return redirect('panel_catalogo')    
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
            total = orden.order_total + orden.envio
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

            descuentos = order.order_total_descuentos
            impuestos = order.order_total_impuestos
            comisiones = order.order_total_comisiones


            order_count_items = ordered_products.count()

            if order_count_items <= 0:
                return redirect('store')

            for cart_item in ordered_products:
                #subtotal += (cart_item.product.price * cart_item.quantity) No se toma precio de lista
                subtotal += (cart_item.product_price * cart_item.quantity)  #Precio ya cerrado
                #subtotal += cart_item.product_price
                quantity += cart_item.quantity

            total =  round(float(subtotal)- float(envio)  - float(descuentos) - float(impuestos) - float(comisiones),2)
             
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
                order.cuenta = cuenta_id
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

        dias_default_movimientos = settings.DIAS_DEFAULT_MOVIMIENTOS
        print("panel_movimientos_list")
        fecha_1=None
        fecha_2=None
        if request.method =="POST":
          
            fecha_1 = request.POST.get("fecha_desde")
            fecha_2 = request.POST.get("fecha_hasta")     
        
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=dias_default_movimientos) 
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

def panel_movimientos_cerrados_list(request,idcierre=None):
    
    if validar_permisos(request,'MOVIMIENTOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    
        mov = Movimientos.objects.filter(idcierre=idcierre).values('cuenta__nombre','cuenta__moneda__simbolo').annotate(total=
        Round(
            Sum('monto'),
            output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__nombre')
        
        movimientos = Movimientos.objects.filter(idcierre=idcierre).order_by('fecha')
        
        context = {
            'mov':mov,
            'movimientos':movimientos,
            'permisousuario':permisousuario
        }
        
        return render(request,'panel/lista_mov_cerrados_cuentas.html',context) 

    else:
        return render (request,"panel/login.html")

def panel_transferencias_list(request):
    
    if validar_permisos(request,'TRANSFERENCIAS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        transf = Transferencias.objects.filter()
        cuentas = Cuentas.objects.all()

        for trans in transf:
            if trans.conversion is None:
                trans.conversion = 1
            if trans.monto_origen is None:
                trans.monto_origen = 0
            if trans.monto_destino is None:
                trans.monto_destino = 0
            
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

        #SI YA EXISTE EL CIERRE EN LA TABLA DE CIERRE BUSCARLO DESDE AHI Y NO RECALCULARLO
        mes = 0
        anio=0
        cuenta=0
        action =""

        if request.method =="POST":
            mes = request.POST.get("mes")
            anio = request.POST.get("anio")
            action = request.POST.get('action')
       
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
    
       
        totales_ingresos_ventas = Movimientos.objects.filter(idcierre__exact=0,ordernumber__isnull=False,movimiento=1,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')

        totales_ingresos_varios = Movimientos.objects.filter(idcierre__exact=0,ordernumber__isnull=True,movimiento=1,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')


        totales_ingresos = Movimientos.objects.filter(idcierre__exact=0,movimiento=1,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')
    
    
        totales_egresos = Movimientos.objects.filter(idcierre__exact=0,movimiento=2,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')


        totales_resultado = Movimientos.objects.filter(idcierre__exact=0,fecha__gte=fecha_desde, fecha__lte=fecha_hasta).values('cuenta__moneda__codigo','cuenta__moneda__simbolo').annotate(total=
            Round(
                Sum('monto'),
                output_field=DecimalField(max_digits=12, decimal_places=2))).order_by('cuenta__moneda')
        
        if action == "ELIMINAR":
            int_mes =  monthToNum(mes)

            cierremensual = CierreMes.objects.filter(mes=int_mes, anio=anio).first()
            if  cierremensual:
                id_cierre = cierremensual.id
                udp_mov =  Movimientos.objects.filter(idcierre__exact=id_cierre)
                for mov in udp_mov:
                    mov.idcierre = 0
                    mov.save()
                cierremensual.delete()
       

    
        if action == "CERRAR":

            int_mes =  monthToNum(mes)
            ing_saldo_pesos = 0
            ing_saldo_dolar = 0
            egr_saldo_pesos = 0
            egr_saldo_dolar = 0
            tot_saldo_pesos = 0
            tot_saldo_dolar = 0

            #Valido que no este hecho el cierre
            for item in totales_ingresos:
                moneda = item['cuenta__moneda__codigo']
                if moneda =="ARS":
                    ing_saldo_pesos = item['total']
                if moneda =="USD":
                    ing_saldo_dolar = item['total']

            for item in totales_egresos:
                moneda = item['cuenta__moneda__codigo']
                if moneda =="ARS":
                    egr_saldo_pesos = item['total']
                if moneda =="USD":
                    egr_saldo_dolar = item['total']

            for item in totales_resultado:
                moneda = item['cuenta__moneda__codigo']
                if moneda =="ARS":
                    tot_saldo_pesos = item['total']
                if moneda =="USD":
                    tot_saldo_dolar = item['total']
           
        
           
            cierremensual = CierreMes.objects.filter(mes=int_mes, anio=anio).first()
            if not cierremensual:
                cierremensual = CierreMes.objects.create(
                    mes=int_mes, 
                    anio=anio, 
                    fecha=datetime.today(),
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    ing_saldo_pesos=ing_saldo_pesos,
                    ing_saldo_dolar=ing_saldo_dolar,
                    egr_saldo_pesos=egr_saldo_pesos,
                    egr_saldo_dolar=egr_saldo_dolar,
                    tot_saldo_pesos=tot_saldo_pesos,
                    tot_saldo_dolar=tot_saldo_dolar
                )
                id_cierre = cierremensual.id
                udp_mov =  Movimientos.objects.filter(idcierre__exact=0,fecha__gte=fecha_desde, fecha__lte=fecha_hasta)
                for mov in udp_mov:
                    mov.idcierre = id_cierre
                    mov.save()
                    

                messages.success(request, f'Se cerró el período ' + str(mes))
            else:
                messages.success(request, f'El período ' + str(mes) +' ya se encuentra cerrado!')

                

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

def panel_balance_movimientos(request):

   
    if validar_permisos(request,'BALANCE'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if request.method =="POST":
            anio = request.POST.get("anio")
        else:
        # Obtener todos los cierres mensuales del año actual (por ejemplo, 2024)
            anio = int(datetime.today().strftime('%Y'))
        print("anio",anio)

        #anios_disponibles = CierreMes.objects.values_list('anio', flat=True).distinct().order_by('-anio')
        yr = int(anio)
        anios_disponibles = [yr-2,yr-1, yr,yr+1,yr+2]

        meses = range(1, 13)  # Meses de 1 (enero) a 12 (diciembre)
        cierres_dict = {cierre.mes: cierre for cierre in CierreMes.objects.filter(anio=anio)}

        
        # Obtener el total de transacciones con idcierre=0 agrupado por mes
        nocerrado_por_mes = (Movimientos.objects.filter(idcierre=0)  # Filtrar transacciones con idcierre=0
                    .annotate(mes=TruncMonth('fecha'))  # Agrupar por mes
                    .values('mes')  # Seleccionar el mes
                    .annotate(total_monto=Sum('monto'))  # Sumar el monto para cada mes
                    .order_by('mes')  # Ordenar por mes
                )
        # Convertir el resultado en un diccionario para un acceso más fácil
        totales_dict = {total['mes'].month: total['total_monto'] for total in nocerrado_por_mes}

        # Inicializar los datos con todos los meses
        data = []
        for mes in meses:
            if mes in cierres_dict:
                cierre = cierres_dict[mes]
                total_movimientos = totales_dict.get(mes, 0)
                data.append({
                    'mes': calendar.month_name[mes],
                    'ingresos_pesos': cierre.ing_saldo_pesos,
                    'ingresos_dolares': cierre.ing_saldo_dolar,
                    'egresos_pesos': cierre.egr_saldo_pesos,
                    'egresos_dolares': cierre.egr_saldo_dolar,
                    'total_pesos': cierre.tot_saldo_pesos,
                    'total_dolares': cierre.tot_saldo_dolar,
                    'total_movimientos': total_movimientos, #Tiene mov no cerrados 
                    'tiene_datos': True,  # Cierre Generado
                    'idcierre':cierre.id,
                })
            else:
                # Si el mes no tiene registro, añadir con valores en 0
                data.append({
                    'mes': calendar.month_name[mes],
                    'ingresos_pesos': 0,
                    'ingresos_dolares': 0,
                    'egresos_pesos': 0,
                    'egresos_dolares': 0,
                    'total_pesos': 0,
                    'total_dolares': 0,
                    'total_movimientos': 0, 
                    'tiene_datos': False,
                    'idcierre':0,
                })

        # Calcular los totales anuales
        totales = {
            'ingresos_pesos': sum(item['ingresos_pesos'] for item in data),
            'ingresos_dolares': sum(item['ingresos_dolares'] for item in data),
            'egresos_pesos': sum(item['egresos_pesos'] for item in data),
            'egresos_dolares': sum(item['egresos_dolares'] for item in data),
            'total_pesos': sum(item['total_pesos'] for item in data),
            'total_dolares': sum(item['total_dolares'] for item in data),
        }

       
        return render(request, 'panel/balance_cuentas.html', {
            'data': data, 
            'totales': totales, 
            'anio': anio, 
            'anios_disponibles': anios_disponibles,
            'permisousuario':permisousuario}
        )
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
    #5 - Costos
    #6 - Lista de Precios
    #7 - Lista de precios Proveedor

        print("Export to Excel",modelo)
        response = HttpResponse(content_type='application/ms-excel')
        if modelo==1:
            response['Content-Disposition']='attachment; filename=Movimientos'+ str(datetime.now()) + '.xls'
        elif modelo==2:
            response['Content-Disposition']='attachment; filename=Pedidos_'+ str(datetime.now()) + '.xls'
        elif modelo==3:
            response['Content-Disposition']='attachment; filename=Articulos_'+ str(datetime.now()) + '.xls'
        elif modelo==4:
            response['Content-Disposition']='attachment; filename=Pedidos_'+ str(datetime.now()) + '.xls'
        elif modelo==5:
            response['Content-Disposition']='attachment; filename=Costos_'+ str(datetime.now()) + '.xls'
        elif modelo==6:
            response['Content-Disposition']='attachment; filename=Precios_'+ str(datetime.now()) + '.xls'
        elif modelo==7:
            response['Content-Disposition']='attachment; filename=Precios_proveedores_'+ str(datetime.now()) + '.xls'
        else:
            response['Content-Disposition']='attachment; filename=Export_'+ str(datetime.now()) + '.xls'
        
        wb = xlwt.Workbook(encoding='utf-8')


        if modelo==1: #MOVIMIENTOS    
            if validar_permisos(request,'EXPORTAR MOVIMIENTOS'):

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

        if modelo==2: #PEDIDOS
            if validar_permisos(request,'EXPORTAR PEDIDOS'):
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
                    columns = ['Pedido','Fecha','Envio','Total','Nombre','Apellido','email','Producto','Cantidad','Precio','Costo','Cuenta','Desc Unit','Precio Unit Cobrado','Origen Venta','Comisiones','Descuentos','Impuestos']
                    for col_num in range(len(columns)):
                        ws.write(row_num,col_num,columns[col_num],font_style)
                    font_style = xlwt.Style.XFStyle()

                    items_pedidos = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta],status=sheet)
                    rows = OrderProduct.objects.filter(order__in=items_pedidos).values_list('order__order_number','order__fecha','order__envio','order__order_total','order__email','order__first_name','order__last_name','product__product_name','quantity','product_price','costo','order__cuenta','descuento_unitario','precio_unitario_cobrado','order__origen_venta__origen','order__order_total_comisiones','order__order_total_descuentos','order__order_total_impuestos')
                     
                    nro_orden_anterior='0'      
                    for row in rows:
                        row_num += 1   
                           
                        for col_num in range(len(row)):              
                            #if col_num==2 or col_num==3 or col_num==8 or col_num==9 or  col_num==10 or col_num==11 or col_num==12 or col_num==13 or col_num==15 or col_num==16 or col_num==17:
                            if col_num in {2, 3, 8, 9, 10, 11, 12, 13, 15, 16, 17}:
                                if col_num ==15: #Comisiones
                                    if nro_orden_anterior==row[0]:
                                        monto = 0
                                    else:
                                        monto = float("{0:.2f}".format((float)(row[col_num])))    
                                else:
                                    monto = float("{0:.2f}".format((float)(row[col_num])))
                                ws.write(row_num,col_num,monto)
                            elif col_num==11:
                                cuentas = Cuentas.objects.filter(id=int(row[col_num])).first()
                                if cuentas:
                                    cuentas = cuentas.nombre
                                else:
                                    cuentas = "Cuenta no asignada"   
                                ws.write(row_num,col_num, str(cuentas),font_style)     
                            else:
                                ws.write(row_num,col_num, str(row[col_num]),font_style)
                        nro_orden_anterior=row[0]

                wb.save(response)
                return response
            else:
                return render (request,"panel/login.html")

        if modelo==3: #PRODCUTOS
            if validar_permisos(request,'EXPORTAR PRODUCTOS'):

                sheet = "productos"

                ws = wb.add_sheet(sheet)
                row_num=0
                font_style= xlwt.Style.XFStyle()
                font_style.font.bold = True
                columns = ['Nombre','slug','Description','Precio','images','stock','Habilitado','Category','Sub Category','peso','ubicacion','Costo']
                for col_num in range(len(columns)):
                    ws.write(row_num,col_num,columns[col_num],font_style)
                font_style = xlwt.Style.XFStyle()
                
                rows = Product.objects.filter().values_list('product_name','slug','description','price','images','stock','is_available','category__category_name','subcategory__subcategory_name','peso','ubicacion','costo_prod').order_by('category__category_name','subcategory__subcategory_name','product_name')
                
                for row in rows:
                    row_num += 1      
                    for col_num in range(len(row)):              
                        if col_num==3 or col_num==5 or col_num==9: #Numericos
                            monto = float("{:.2f}".format(float(row[col_num])))
                            ws.write(row_num,col_num,monto)
                        else:
                            ws.write(row_num,col_num, str(row[col_num]),font_style)
                    
                wb.save(response)
                return response
            else:
                return render (request,"panel/login.html")

        if modelo==4: #PEDIDOS  TEMP  (DE LA TABLA TEMPORAL)
            if validar_permisos(request,'EXPORTAR PEDIDOS'):
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

        if modelo==5: #COSTOS 
            if validar_permisos(request,'EXPORTAR COSTOS'):
                sheet = "Costos"
                ws = wb.add_sheet(sheet)
                
                row_num=0
                font_style= xlwt.Style.XFStyle()
                font_style.font.bold = True
                columns = ['Producto','Costo','Fecha de Actualización','Usuario']
                for col_num in range(len(columns)):
                    ws.write(row_num,col_num,columns[col_num],font_style)
                font_style = xlwt.Style.XFStyle()

                rows = Costo.objects.all().values_list('producto__product_name','costo','fecha_actualizacion','usuario__email').order_by('-fecha_actualizacion','producto__product_name')
     
                for row in rows:
                    row_num += 1      
                    for col_num in range(len(row)):
                        if col_num==2:
                            format_string = '%Y-%m-%d %H:%M:%S.%f'
                            str_fecha = str(row[col_num])
                            str_fecha = datetime.strptime(str_fecha, format_string)
                            ws.write(row_num,col_num,str(str_fecha),font_style)
                        elif col_num==1:
                            monto = float("{0:.2f}".format((float)(row[col_num])))
                            ws.write(row_num,col_num,monto)
                        else:
                            ws.write(row_num,col_num,str(row[col_num]),font_style)
                        
                wb.save(response)
                return response
            else:
                return render (request,"panel/login.html")
        
        if modelo==6: #LISTA DE PRECIOS 
            sheet = "Precios"
            ws = wb.add_sheet(sheet)
            
            row_num=0
            font_style= xlwt.Style.XFStyle()
            font_style.font.bold = True
            #columns = ['Producto','Marca','Costo','Precio Base','Precio Web (Regular)','Com 1 WEB','Gan Venta Web','Precio Estimado Tienda Nube','Precio Tienda Nube','Com 2 Tienda Nube','Gan Tienda Nube','Precio Estimado Mercado LibreL','Precio Mercado Libre','Com 3 ML','Gan Mercado Libre']
            columns = [
                'Producto', 'Marca', 'Costo', 'Stock', 'Precio Base', 'Precio Web (Regular)', 
                'Com 1 WEB', 'Gan Venta Web', 'Precio Estimado Tienda Nube', 
                'Precio Tienda Nube', 'Com 2 Tienda Nube', 'Gan Tienda Nube', 
                'Precio Estimado Mercado Libre', 'Precio Mercado Libre', 
                'Com 3 ML', 'Gan Mercado Libre'
                ]
            for col_num in range(len(columns)):
                ws.write(row_num,col_num,columns[col_num],font_style)
            font_style = xlwt.Style.XFStyle()

            # Obtener los valores de los márgenes con código MG1, MG2 y MG3
            margen1 = ConfiguracionParametros.objects.get(codigo='MG1')
            margen2 = ConfiguracionParametros.objects.get(codigo='MG2')
            margen3 = ConfiguracionParametros.objects.get(codigo='MG3')
            #COMISIONES DE VENTA  1 (Regular / Informal) 2 (Tienda Nube) 3 (Mercado Libre)
            comision1 = ConfiguracionParametros.objects.get(codigo='COM1')
            comision2 = ConfiguracionParametros.objects.get(codigo='COM2')
            comision3 = ConfiguracionParametros.objects.get(codigo='COM3')
            
            #COSTO FIJO x VENTA ML
            costo3_menor = ConfiguracionParametros.objects.get(codigo='CST3_1') # Monte menor a 12000
            costo3_mayor = ConfiguracionParametros.objects.get(codigo='CST3_2') # Monto mayor a 12000
            
            if not comision1:
                comision1=0
            if not comision2:
                comision2=0
            if not comision3:
                comision3=0
            if not costo3_menor:
                costo3_menor = 0
            if not costo3_mayor:
                costo3_mayor = 0


            try:
                # Verificar si los valores son porcentaje o valor monetario y anotarlos en el queryset
                rows = Product.objects.filter().values_list('product_name','subcategory__subcategory_name','costo_prod','stock','price','precio_TN','precio_ML').annotate(
                    # Cálculo del margen1 (costo + (costo * margen1 / 100))
                    precio_base=ExpressionWrapper(
                        F('costo_prod') * (float(margen1.valor) / 100) + F('costo_prod'),
                        output_field=FloatField()
                        ),
                    comision1_calculado=ExpressionWrapper(
                        F('price') * (float(comision1.valor) / 100),  # Precio de Venta Regular * Comision
                        output_field=FloatField()
                        ),
                    beneficio1_calculado=ExpressionWrapper(
                        F('price') - F('costo_prod') -F('comision1_calculado'),output_field=FloatField()
                        ),
                    # Cálculo del margen2 (precio_base + (precio_base * margen2 / 100))
                    precio_cal_tn=ExpressionWrapper(
                        F('precio_base') * (float(margen2.valor) / 100) + F('precio_base'),
                        output_field=FloatField()
                        ),
                    comision2_calculado=ExpressionWrapper(
                        F('precio_TN') * (float(comision2.valor) / 100),  # Precio de Venta Tienda Nube * Comision
                        output_field=FloatField()
                        ),
                    beneficio2_calculado=ExpressionWrapper(
                        F('precio_TN') - F('costo_prod') -F('comision2_calculado'),output_field=FloatField()
                        ),
                    # Cálculo del margen3 (precio_tn + (precio_tn * margen3 / 100))
                    precio_cal_ml=ExpressionWrapper(
                        F('precio_base') * (float(margen3.valor) / 100) + F('precio_base'),
                        output_field=FloatField()
                            ),
                    # Cálculo condicional de la comisión3 según el valor de precio_ML
                    comision3_calculado=ExpressionWrapper(
                        F('precio_ML') * (float(comision3.valor) / 100) + 
                        Case(
                            When(Q(precio_ML__gt=12000), then=Value(float(costo3_mayor.valor))),
                            default=Value(float(costo3_menor.valor)),
                            output_field=FloatField()
                        ),
                        output_field=FloatField()
                    ),
                    beneficio3_calculado=ExpressionWrapper(
                        F('precio_ML') - F('costo_prod') -F('comision3_calculado'),output_field=FloatField()
                        )
                    ).order_by('product_name')
            
            except ConfiguracionParametros.DoesNotExist:
                # En caso de que no exista alguno de los márgenes, manejar la excepción.
                rows = Product.objects.all().values_list('product_name','subcategory__subcategory_name','costo_prod','price','precio_TN','precio_ML').order_by('product_name')
            #rows = Costo.objects.all().values_list('producto__product_name','costo','fecha_actualizacion','usuario__email').order_by('-fecha_actualizacion','producto__product_name')
            for row in rows:
                row_num += 1
                # Reorganiza los campos del queryset según el orden que deseas en el Excel
                data_row = [
                    row[0],  # Producto (product_name)
                    row[1],  # Marca (subcategory__subcategory_name)
                    row[2],  # Costo (costo_prod)
                    row[3],  # Precio de Venta Regular (price)
                    row[7],  # Precio Base (precio_cal_tn)
                    row[4],  # Precio Web (Regular) (price)
                    row[8],  # Com 1 WEB (comision1_calculado)
                    row[9], # Gan Venta Web (beneficio1_calculado)
                    row[10],  # Precio Estimado Tienda Nube (precio_cal_tn)
                    row[5],  # Precio Tienda Nube (precio_TN) (4)
                    row[11],  # Com 2 Tienda Nube (comision2_calculado)
                    row[12], # Gan Tienda Nube (beneficio2_calculado)
                    row[13], # Precio Estimado Mercado Libre (precio_cal_ml)
                    row[6],  # Precio Mercado Libre (precio_ML)
                    row[14], # Com 3 ML (comision3_calculado)
                    row[15]  # Gan Mercado Libre (beneficio3_calculado)
                ]
                # Escribir la fila en el archivo Excel
                for col_num, value in enumerate(data_row):
                    if row_num == 4:
                        print(row_num, col_num, str(value))
                    if col_num == 0 or col_num == 1:
                        ws.write(row_num, col_num, str(value), font_style)
                    else:
                        monto = float("{0:.2f}".format((float)(value)))
                        ws.write(row_num, col_num, monto)
                    
            wb.save(response)
            return response

        if modelo==7: #LISTA DE PRECIOS PROVEEDORES 
            if validar_permisos(request,'PROVEEDORES'):
                sheet = "Proveedores"
                ws = wb.add_sheet(sheet)
                
                row_num=0
                font_style= xlwt.Style.XFStyle()
                font_style.font.bold = True
                columns = ['Proveedor','Articulo','Marca','Precio','Producto Qualities','Stock Actual']
                for col_num in range(len(columns)):
                    ws.write(row_num,col_num,columns[col_num],font_style)
                font_style = xlwt.Style.XFStyle()

               
                rows = ProveedorArticulos.objects.all().values_list('proveedor__nombre','nombre_articulo','marca__marca','precio_por_unidad','id_product__product_name','id_product__stock').order_by('nombre_articulo','precio_por_unidad')
          
                for row in rows:
                    row_num += 1      
                    for col_num in range(len(row)):
                        if col_num==100:
                            format_string = '%Y-%m-%d %H:%M:%S.%f'
                            str_fecha = str(row[col_num])
                            str_fecha = datetime.strptime(str_fecha, format_string)
                            ws.write(row_num,col_num,str(str_fecha),font_style)
                        elif col_num==3 or col_num ==5:
                            if row[col_num] is None:
                                monto = float("{0:.2f}".format((float)(0)))
                                ws.write(row_num,col_num,monto)
                            else:
                                monto = float("{0:.2f}".format((float)(row[col_num])))
                                ws.write(row_num,col_num,monto)
                        else:
                            ws.write(row_num,col_num,str(row[col_num]),font_style)
                        
                wb.save(response)
                return response
            else:
                return render (request,"panel/login.html") 
                   
def articulos_vendidos_export_xls(request):
    
        fecha_1 = request.POST.get("fechadesde")
        fecha_2 = request.POST.get("fechahasta")     

        print(fecha_1,fecha_2)    
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=90) 
            fecha_desde = fecha_hasta - dias
        else:      
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')


        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition']='attachment; filename=Export_'+ str(datetime.now()) + '.xls'
        
        wb = xlwt.Workbook(encoding='utf-8')

        sheet = "Articulos"
        ws = wb.add_sheet(sheet)
        
        row_num=0
        font_style= xlwt.Style.XFStyle()
        font_style.font.bold = True
        columns = ['Producto','Cantidad Vendida','Precio Unitario']
        for col_num in range(len(columns)):
            ws.write(row_num,col_num,columns[col_num],font_style)
        font_style = xlwt.Style.XFStyle()

        items_pedidos = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta])
        rows = OrderProduct.objects.filter(order__in=items_pedidos).values_list('product__product_name').annotate(
            cantidad=Round(Sum('quantity')),
            importe=Sum('product_price')).order_by('-cantidad')
        
        # `rows` ya es una lista de tuplas, por lo que no necesitas hacer más conversiones
        resultados = rows
        row_num = 0
        for row in resultados:
            row_num += 1      
            for col_num in range(len(row)):
                if col_num == 2 or col_num == 3:
                    monto = float("{0:.2f}".format(float(row[col_num])))
                    ws.write(row_num, col_num, monto)
                else:
                    ws.write(row_num, col_num, str(row[col_num]), font_style)
                        
        wb.save(response)
        return response

def clientes_ventas_export_xls(request):
    
        fecha_1 = request.POST.get("fechadesde")
        fecha_2 = request.POST.get("fechahasta")     

        print(fecha_1,fecha_2)    
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=90) 
            fecha_desde = fecha_hasta - dias
        else:      
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')


        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition']='attachment; filename=Export_'+ str(datetime.now()) + '.xls'
        
        wb = xlwt.Workbook(encoding='utf-8')

        sheet = "Costos"
        ws = wb.add_sheet(sheet)
        resultados = []
        row_num=0
        font_style= xlwt.Style.XFStyle()
        font_style.font.bold = True
        columns = ['Apellido','Nombre','Importe total','Cantidad']
        for col_num in range(len(columns)):
            ws.write(row_num,col_num,columns[col_num],font_style)
        font_style = xlwt.Style.XFStyle()

        #values_list => Agrupa => lista de tuplas
        #values = No agrupa  => Diccionario
        rows = Order.objects.filter(fecha__range=[fecha_desde, fecha_hasta]).values_list('last_name', 'first_name').annotate(
        total=Round(
            Sum('order_total'),
            output_field=DecimalField(max_digits=12, decimal_places=2)),cantidad=Count('order_number')).order_by('-total')

        # `rows` ya es una lista de tuplas, por lo que no necesitas hacer más conversiones
        resultados = rows
        row_num = 0
        for row in resultados:
            row_num += 1      
            for col_num in range(len(row)):
                if col_num == 2 or col_num == 3:
                    monto = float("{0:.2f}".format(float(row[col_num])))
                    ws.write(row_num, col_num, monto)
                else:
                    ws.write(row_num, col_num, str(row[col_num]), font_style)
                        
        wb.save(response)
        return response
         
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
                print("*****IMPORTAR PRODUCTOS*************")
                #Get the first sheet in the workbook by index
                sheet1 = workbook.sheet_by_index(0)

                #Borro todo lo anterior
                tmp_producto = ImportTempProduct.objects.filter(usuario = request.user)
                if tmp_producto:
                    tmp_producto.delete()
                print("tabla temporal borrada")
                #Get each row in the sheet as a list and print the list
                for rowNumber in range(sheet1.nrows):
                    try:
                        #row = sheet1.row_values(rowNumber)
                        dato = sheet1.cell_value(rowNumber, 0)
                        print( "dato.lower()", dato.lower())
                        if dato.lower().strip() != 'producto' and dato.lower().strip() != 'nombre':    
                            
                            product_name = sheet1.cell_value(rowNumber, 0)
                            product_name = product_name.strip()
                            slug_product = product_name.replace('ñ','enie')
                            slug_product = product_name.replace('Ñ','eniee')

                            tmp_producto = ImportTempProduct.objects.filter(product_name=product_name, usuario = request.user).first()
                            if not tmp_producto:
                                print("Producto no existe en temp, ...:")
                                #Valido que exista la categoria
                                cat_name = sheet1.cell_value(rowNumber, 7).strip()
                                print("Category:", cat_name)

                                sub_cat_name = sheet1.cell_value(rowNumber, 8).strip()
                                print("sub cat", sub_cat_name)
                                img_name = sheet1.cell_value(rowNumber, 4)
                                print("img_name", img_name)

                                if not img_name:
                                    img_name = 'none.jpg'
                                else:
                                    img_name = img_name.replace(' ', '%20')
                                    
                                img_name = img_name.strip()

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
                                    #print("Tengo cat",cat.id)
                                    if not sub_cat:
                                        #print("No teng subcat",slug_cat)
                                       
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

                                        int_peso = sheet1.cell_value(rowNumber, 9)
                                        float_peso = float("{0:.2f}".format(float(int_peso)))
                                        #print("float_peso",float_peso)

                                        valor_ubicacion = sheet1.cell_value(rowNumber, 10)
                                        # Convertimos a cadena eliminando el ".0" en caso de ser número flotante
                                        if isinstance(valor_ubicacion, float):
                                            str_ubicacion = str(int(valor_ubicacion))
                                        else:
                                            str_ubicacion = str(valor_ubicacion)

                                        #print("str_ubicacion_2", str_ubicacion)


                                        int_costo = sheet1.cell_value(rowNumber, 11)
                                        f_costo = float("{0:.2f}".format((float)(int_costo)))
                                        #print("f_costo",f_costo)

                                        int_precio = sheet1.cell_value(rowNumber, 3)
                                        f_precio = float("{0:.2f}".format((float)(int_precio)))
                                        #print("f_precio",f_precio)

                                        int_stock = sheet1.cell_value(rowNumber, 5)
                                        f_stock = float("{0:.0f}".format((float)(int_stock)))
                                        #print("f_stock",f_stock)

                                        description= sheet1.cell_value(rowNumber, 2)
                                        description = description.strip()
                                        
                                        tmp_producto = ImportTempProduct(
                                            product_name=product_name,
                                            slug=slugify(slug_product).lower(),
                                            description= description,
                                            variation_category = "", #sheet1.cell_value(rowNumber, 2),
                                            variation_value = "", #sheet1.cell_value(rowNumber, 3),
                                            price=f_precio,
                                            images=img_name,
                                            stock=f_stock,
                                            is_available=sheet1.cell_value(rowNumber, 6),
                                            category=cat.category_name, #  sheet1.cell_value(rowNumber, 8),
                                            subcategory=sub_cat.subcategory_name,# sheet1.cell_value(rowNumber, 9),
                                            created_date= datetime.today(),
                                            modified_date=datetime.today(),
                                            usuario = request.user,
                                            peso = float_peso,
                                            ubicacion= str(str_ubicacion),
                                            costo_prod=f_costo
                                                )
                            
                                        tmp_producto.save()
                                        print("Save temp producto, UBICACION:", str_ubicacion, " Costo: " , str(f_costo))
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
                            print("Fin proceso linea..")
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
                        dato = sheet1.cell_value(rowNumber, 0)
                        if dato.lower() != "producto": # Saco la primera file
                            producto = sheet1.cell_value(rowNumber, 0)
                            precio = sheet1.cell_value(rowNumber, 1)
                            
                            try:
                                
                                precio = float(precio)
                                
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
                                        imgfile = tmp_producto.images,
                                        images=tmp_producto.images,
                                        stock=tmp_producto.stock,
                                        is_available=tmp_producto.is_available,
                                        category=tmp_producto.category,
                                        subcategory=tmp_producto.subcategory,
                                        created_date=tmp_producto.created_date,
                                        modified_date=datetime.today() ,
                                        is_popular = False, 
                                        peso = tmp_producto.peso, 
                                        ubicacion = tmp_producto.ubicacion,                                     
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
                        dato = sheet1.cell_value(rowNumber, 0)
                        if dato.lower() != "producto": # Saco la primera file
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
                                        imgfile=tmp_producto.images,
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
    cant_art_nuevos = 0
    cant_art_actualizados = 0

    if articulos_tmp:
        for a in articulos_tmp:
            try:
                producto = Product.objects.filter(product_name=a.product_name)
                category = Category.objects.get(category_name=a.category)
                #Agrego
                if not producto:
                    if not a.images:
                      imagen = "photos/products/none.jpg" #default      
                    else:
                        imagen = a.images
                    #print("Guardar_tmp_productos",a.product_name,a.ubicacion,a.costo_prod)
                    producto = Product(
                        product_name = a.product_name.strip(),
                        slug=a.slug,
                        description = a.description.strip(),
                        category = category,
                        subcategory = SubCategory.objects.get(category=category,subcategory_name=a.subcategory),
                        images = imagen,
                        imgfile = imagen,
                        stock = a.stock,
                        price = float(a.price),
                        is_available = a.is_available,
                        created_date= datetime.today(),
                        modified_date=datetime.today(),
                        peso = a.peso, 
                        ubicacion= a.ubicacion,
                        costo_prod =  float(a.costo_prod)
                    )
                    producto.save()
                    cant_art_nuevos = cant_art_nuevos +  1
                else:
                    #Actualizo
                    producto = Product.objects.get(product_name=a.product_name.strip())
                    producto.category = category
                    producto.subcategory = SubCategory.objects.get(category=category,subcategory_name=a.subcategory)
                    producto.images = a.images
                    producto.stock = float(a.stock)
                    producto.price = float(a.price)
                    producto.is_available = a.is_available
                    producto.peso = float(a.peso)
                    producto.ubicacion = a.ubicacion
                    producto.costo_prod = float(a.costo_prod)
                    producto.save()
                    cant_art_actualizados = cant_art_actualizados + 1

                    
            except ObjectDoesNotExist:
                print ("Error en Tmp_articulos ", a.product_name )
                
            except Exception as err:
                print(a.product_name, f"guardar_tmp_productos {err=}, {type(err)=}")


        messages.success(request, f'Articulos importados con éxito! Nuevos: ' + str(cant_art_nuevos) + ' Actualizados: ' + str(cant_art_actualizados))

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
            
            nombre = request.POST['nombre'].strip()
            description = request.POST['description'].strip()
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
            cat_nombre = request.POST.get("category_name").strip()
            cat_descripcion = request.POST.get("description").strip()
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

def panel_validar_producto_default(request,product_name):
    # Valida que exista el producto, caso contrario lo agrega al maestro para poder hacer la importación de los pedidos.
    try:
        # Intentamos obtener el producto por su slug
        slug_product = product_name.replace('ñ','enie')
        slug_product = product_name.replace('Ñ','eniee')
        producto = Product.objects.get(slug=slugify(slug_product).lower())
        return True  # El producto existe

    except Product.DoesNotExist:
        # Si no existe, se procede a agregarlo
        try:
            category_slug=settings.DEF_CATEGORY_ADD_PROD
            subcategory_slug=settings.DEF_SUBCATEGORY_ADD_PROD

            slug_product = product_name.replace('ñ','enie')
            slug_product = product_name.replace('Ñ','eniee')
            #Genero un producto propio en base a los datos del producto del proveedor
            category = Category.objects.filter(slug=category_slug).first()
            subcategory = SubCategory.objects.filter(category=category,sub_category_slug=subcategory_slug).first()
            producto = Product(
                product_name=product_name,
                slug=slugify(slug_product).lower(),
                description=product_name,
                price=1,
                images='none.jpg',  # Cambié .fpg a .jpg (posiblemente un error tipográfico)
                imgfile='none.jpg',
                stock=0,
                is_available=False,
                category=category,
                subcategory=subcategory,
                created_date=datetime.today(),
                modified_date=datetime.today(),
                peso=0,
                costo_prod=1,
                ubicacion='',
                precio_TN=0,
                precio_ML=0
            )
            producto.save()
            return True  # El producto fue agregado correctamente

        except Exception as e:
            # Si hay algún error durante la creación o el guardado, retorna False
            return False

    except Exception as e:
        # Si hay algún otro error inesperado, retorna False
        return False

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
                    cell_value = sheet1.cell_value(rowNumber, 0)
                    codigo = ''.join(cell_value.split()).lower()
                    if codigo:
                        codigo = ''.join(cell_value.split()).lower()
                        if codigo != "codigo":  #Paso el encabezado
                            print("Linea ",rowNumber," codigo: ",codigo)
                            codigo = codigo.upper().strip()
                            pedidos_tmp = ImportTempOrders.objects.filter(codigo=codigo, usuario = request.user).first()
                            if not pedidos_tmp:
                                #print("Obteniendo datos de la linea")
                                try:
                                    str_field       = "Tipo correo"
                                    correo = sheet1.cell_value(rowNumber, 6)  #Tipo Correo #1 OCA # 2CA # 3 Retira Cliente
                                    if correo in ['1', '2', '3']:
                                        tipo_correo = int(correo)
                                    else:
                                        tipo_correo = 2

                                    nombre_completo= str(sheet1.cell_value(rowNumber, 5))
                                    i_end = nombre_completo.find(" ")
                                    nombre = nombre_completo[0:i_end]
                                    apellido = nombre_completo[i_end:len(nombre_completo)]
                                    #Tomo los datos de la linea
                                    str_field   = "first_name"
                                    first_name  = nombre
                                    #print("first_name",first_name)
                                    str_field   = "Nombre"
                                    last_name   = apellido
                                    #print("last_name",last_name)

                                    str_field   = "email"
                                    cell_value = sheet1.cell_value(rowNumber, 7) #email
                                    if cell_value:
                                        email = str(cell_value).strip()
                                    else:
                                        email = None
                                    
                                     
                                    str_field   = "date"
                                    cell_value = sheet1.cell_value(rowNumber, 1) #fecha
                                    if cell_value:
                                        created_date = str(cell_value).strip()
                                        modified_date = str(cell_value).strip()
                                    else:
                                        created_date = datetime.today()
                                        modified_date = datetime.today()

                                    str_field  = "Order Total"
                                    cell_value = sheet1.cell_value(rowNumber, 2) #Order Total
                                    if cell_value:
                                        order_total = float(cell_value)
                                        
                                    else:
                                        order_total = None
                                   
                                    str_field  = "Telefono"
                                    cell_value = sheet1.cell_value(rowNumber, 12) #Telefono
                                    if cell_value:
                                        dir_telefono = str(cell_value).strip()
                                    else:
                                        dir_telefono = ''

                                    
                                    str_field  = "Calle"
                                    cell_value = sheet1.cell_value(rowNumber, 8) #Calle
                                    if cell_value:
                                        dir_calle = str(cell_value).strip()
                                    else:
                                        dir_calle = ''

                                    dir_nro             = "0"
                                    str_field  = "Localidad"
                                    cell_value = sheet1.cell_value(rowNumber, 9) #Localidad
                                    if cell_value:
                                        dir_localidad = str(cell_value).strip()
                                    else:
                                        dir_localidad = ''
                                   
                                    str_field  = "Provincia"
                                    cell_value = sheet1.cell_value(rowNumber, 11) #Provincia
                                    if cell_value:
                                        dir_provincia = str(cell_value).strip()
                                    else:
                                        dir_provincia = ''
                                   
                                    str_field  = "CP"
                                    cell_value = sheet1.cell_value(rowNumber, 10) #CP
                                    if cell_value:
                                        dir_cp = str(cell_value).strip()
                                    else:
                                        dir_cp = ''

                                    str_field  = "Obs"
                                    cell_value = sheet1.cell_value(rowNumber, 13) #Observaciones
                                    if cell_value:
                                        dir_obs = str(cell_value).strip()
                                    else:
                                        dir_obs = ''

                                    usuario             = request.user
                                    #LISTADO DE ARTICULOS
                                    mensaje = sheet1.cell_value(rowNumber, 4)
                                    #print(correo,first_name,email,created_date,modified_date,order_total,dir_telefono,dir_calle,dir_nro,dir_localidad,dir_provincia,dir_cp,dir_obs)
                                    encabezado = False
                                    
                                    new_pedido = ImportTempOrders.objects.filter(codigo=codigo)
                                    if not new_pedido:
                                        try:
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
                                                dir_tipocorreo  = tipo_correo,
                                                usuario        = request.user,
                                                status          = False
                                                )                                    
                                            new_pedido.save()
                                            encabezado = True
                                            print("Pedido creado en temporal ****************")
                                        except Exception as e:
                                            # Manejar el error aquí
                                            print(f"Error al guardar el pedido: {e}")
                                            encabezado = False
                                            error_str= error_str + "codigo:" + str(codigo) + " - " + f"Error al guardar el pedido: {e}" + "   "
                                            cant_error=cant_error+1
                                        if encabezado:       
                                            #LINEAS DE ARTICULOS
                                            #print("--> DETALLE DEL PEDIDO MENSAJE:<--",mensaje)                                
                                            if "?pedido=" in mensaje:
                                                i_start_ped = mensaje.find('?pedido=')
                                                i_end_ped = mensaje.find('*',i_start_ped)
                                                codigo_ped = mensaje[i_start_ped + 8 :i_end_ped]
                                                #print("Codigo Detalle",codigo_ped,codigo)
                                            
                                            if codigo.lower().strip() == codigo_ped.lower().strip():
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

                                                    try:
                                                            #Validar si el articulo existe sino lo agrega.
                                                            resultado = panel_validar_producto_default(request, product)
                                                            if resultado:
                                                            
                                                                new_linea_pedido = ImportTempOrdersDetail(
                                                                    codigo = new_pedido,
                                                                    product = product,
                                                                    quantity = quantity,
                                                                    subtotal = subtotal,
                                                                    usuario = usuario,
                                                                    status = False
                                                                    )
                                                                new_linea_pedido.save()
                                                            else:
                                                                #Agrego producto


                                                                #Producto no catalogado
                                                                print("Producto no catalogado",product)
                                                                error_str= error_str + 'Artículo: ' + product + ' Linea: ' + str(i) + " NO Catalogado. // " 
                                                                cant_error=cant_error+1
                                                    except Exception as err:
                                                        error_str= error_str + 'Artículo: ' + product + ' Linea: ' + str(i) + " No se pudo obtener del mensaje // "
                                                       
                                                        cant_error=cant_error+1
                                                    mensaje = mensaje[i_end_ped:len(mensaje)]
                                                
                                        else:
                                            print("Pedido no grabado",codigo)

                                except Exception as err:
                                    error_str= error_str + codigo + " linea: " + str(rowNumber) + " campo: " + str_field + " // "
                                  
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
                        slug_product = product_name.replace('ñ','enie')
                        slug_product = product_name.replace('Ñ','eniee')
                        slug=slugify(slug_product).lower()
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
                dir_tipocorreo= enc.dir_tipocorreo,
                order_total = order_total,
                status = status_enc 
            ) 
            #print("encabezado updated_at:", encabezado.updated_at)
            encabezado.save()
                          
def guardar_tmp_pedidos(request,codigo=None):
    
    if codigo:
        #Importar 1
        cant_error=0
        error_str=''
        print("Guardar pedido: ",codigo)
        pedidos_tmp = ImportTempOrders.objects.filter(usuario=request.user,codigo=codigo).first()
        if pedidos_tmp:
            id_temp_pedido=pedidos_tmp.id
            order = Order.objects.filter(order_number=codigo)
            if not order:
                print("El pedido no existe, lo grabo",id_temp_pedido)
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
                        dir_tipocorreo= pedidos_tmp.dir_tipocorreo,
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
                    print("Encabezado: id", Order_New.id)
                    if Order_New:
                            print("Inicio detalle...",id_temp_pedido)
                            detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo_id=id_temp_pedido, usuario=request.user)
                            total_arts = 0
                            for item in detalle_tmp:
                               
                                chk_prod= Product.objects.filter(product_name=item.product).first()
                                if chk_prod:
                                    producto = Product.objects.get(product_name=item.product)
                                    print("Producto del Detalle:" , producto)
                                    if producto:
                                        Order_Det_New = OrderProduct(
                                                order = Order_New,
                                                user = request.user,
                                                product = producto,
                                                quantity = item.quantity,
                                                product_price = item.subtotal / item.quantity,  # EN LA IMPOSTARCION VIENE EL TOTAL NO PRECIO UNITARIO
                                                ordered = True,
                                                descuento_unitario = 0,
                                                precio_unitario_cobrado =item.subtotal / item.quantity,     #Precio Unitario Cobrado sin impuestos ni comisiones
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
                                else:
                                    cant_error = cant_error + 1
                                    error_str = error_str + " Orden:" + str( codigo) + ". Articulo no encontrado: " + str(producto) + "  Cant: " + str(item.quantity)
                                    print("Producto no encontrado en el maestro:" , producto)
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
                    detalle_tmp =  detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo=id_pedido, usuario=request.user)
                    if detalle_tmp:
                        detalle_tmp.delete()
                    
    #Si tiene acceso a PANEL
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
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

def guardar_tmp_pedidos_all(request):
      
    pedidos_tmp = ImportTempOrders.objects.filter(usuario = request.user).order_by('codigo')
    if pedidos_tmp:
        for pedido in pedidos_tmp:
            codigo = pedido.codigo
            pedidos_tmp = ImportTempOrders.objects.filter(usuario=request.user,codigo=codigo).first()
            if pedidos_tmp:
                id_temp_pedido=pedidos_tmp.id
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
                            dir_tipocorreo= pedidos_tmp.dir_tipocorreo,
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
                                detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo=id_temp_pedido, usuario=request.user)
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
                                                    descuento_unitario = 0,
                                                    precio_unitario_cobrado =item.subtotal / item.quantity, 
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
                                if i_end > 0:
                                    usr_name = usr_name[1:i_end]
                                
                                print("usr_name",usr_name)
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


                        #if pedidos_tmp:
                        #    print("1.Borro temp Pedidos:",id_pedido)
                        #    pedidos_tmp.id = id_pedido
                        #    pedidos_tmp.delete()
                        #if detalle_tmp:
                        #    print("Borro temp Pedidos detalle")
                        #    detalle_tmp.delete()
                    

                    #if pedidos_tmp:
                    #    print("2.Borro temp Pedidos",id_pedido)
                    #    pedidos_tmp.id = id_pedido
                    #    pedidos_tmp.delete()
                    #    detalle_tmp =  detalle_tmp = ImportTempOrdersDetail.objects.filter(codigo=id_temp_pedido, usuario=request.user)
                    #    if detalle_tmp:
                    #        detalle_tmp.delete()
            


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
                    print("id pago:",id_pago)
                    if pago:
                        print("Busco movimientos")
                        try:
                            movimiento = Movimientos.objects.get(ordernumber=id_orden)
                            if movimiento:  
                                
                                id_mov = movimiento.id
                                id_cierre = movimiento.idcierre
                                print("movimientos")
                                if id_cierre is None or id_cierre == 0:
                                    print("Mov --> ",id_mov )
                                    movimiento.id = id_mov
                                    movimiento.delete()
                                else:
                                    messages.error(request,"No se puede elimiar el pago. el período está cerrado",'red')
                                    return redirect('panel_pedidos','New')
                            else:
                                print("Error al eliminar el movimiento")

                        except:
                            print("No se encontraton movimientos")

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

        try:
            if order_number:
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

            #Esto es porque cuando esta desabilitado el campo conversion porque transfiere misma moneda
            if not conversion:
                conversion = 1

            
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
                    delete_transf = False
                    mov1 = Movimientos.objects.filter(idtransferencia=idtransfer).all()
                    for mov in mov1:
                        if mov.idcierre==0:
                            mov1.delete()
                            delete_transf = True
                        
                    if delete_transf == True:
                        trans.delete()
                    else:
                        messages.error(request,"No se puede eliminar un movimiento cerrado.","red")
            
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
                    if movimiento.idcierre==0:
                        movimiento.delete()
                    else:
                        messages.error(request,"No se puede eliminar un movimiento cerrado.","red")
                  
        return redirect('panel_movimientos')     
    else:
            return render (request,"panel/login.html")

def panel_pedidos_modificar(request,order_number=None,item=None,quantity=None):
    
    if validar_permisos(request,'PEDIDOS EDIT'):
            print("panel_pedidos_modificar")
            if quantity == 0:
                messages.error(request, "La cantidad no puede ser cero.")
                return redirect('pedidos/detalle/edit/' + order_number)

            
            producto = Product.objects.filter(pk=item).first()
            if producto:

                product_price = producto.price
                product_costo = producto.costo_prod
                
                try:
                    if order_number:
                        print("order number",order_number)
                        pedido = Order.objects.get(order_number=order_number)
                        if pedido:
                            id_pedido = pedido.id
                            #Si existe elimino el registro
                            existe = OrderProduct.objects.filter(order_id=id_pedido,product=producto).exists()
                            if existe:
                                print("Existe")
                                articulos = OrderProduct.objects.filter(order_id=id_pedido).first()
                                articulos = OrderProduct (
                                    id = articulos.id,
                                    order = pedido,
                                    user = request.user,
                                    product = producto,
                                    quantity = articulos.quantity + float(quantity),
                                    product_price = product_price,
                                    precio_unitario_cobrado=product_price,
                                    updated_at =  datetime.today(),
                                    created_at = articulos.created_at,
                                    costo = articulos.costo
                                )
                                articulos.save()
                                
                                #SI EL ARTICULO EXISTE SUMO CANTIDAD ANTERIOR Y RESTO ACTUAL AL STOCK 
                                product = Product.objects.get(id=item)
                                if product:
                                    #       Stock Actual +  Stock Linea Orig  - Cantidad Nueva
                                    saldo = float(product.stock) + float(articulos.quantity) - float(quantity)
                                    product.stock = float(saldo)
                                    product.save()
                                   
                            else:    
                                print("No existe")
                                articulos = OrderProduct (
                                    order = pedido,
                                    user = request.user,
                                    product = producto,
                                    quantity = quantity,
                                    product_price = product_price,
                                    precio_unitario_cobrado=product_price,
                                    updated_at =  datetime.today(),
                                    costo = product_costo
                                )
                                articulos.save()

                                #SI EL ARTICULO NO EXISTE RESTO ACTUAL AL STOCK 
                                product = Product.objects.get(id=item)
                                if product:
                            
                                    product.stock -= float(quantity)
                                    product.save()


                                if producto.es_kit:
                                    print("Es Kit. articulos.id:", articulos.id)

                                    #Guardo en OrderProductKits
                                    #Busco datos  del KIT
                                    kits = ProductKitEnc.objects.filter(productokit=item).first()
                                    if kits:
                                        cantidad = kits.cant_unidades
                                        id_enc_kit = kits.id
                                        item_kits = ProductKit.objects.filter(productokit=id_enc_kit)    
                                        for item_kit in item_kits:
                                            #Busco Componenetes
                                            
                                            orderproduct = OrderProduct.objects.get(id=articulos.id)
                                            OrderProductKitItem.objects.create(order_product=orderproduct,product=item_kit.productohijo, quantity=cantidad)
                                            # Redusco Stock de los articulos Kits
                                            product = Product.objects.get(id=item_kit.productohijo)
                                            if product:
                                                #pesoarticulos += product.peso * item.quantity 
                                                product.stock = product.stock - cantidad
                                                product.save()




                                    items_kits = OrderProductKitItem.objects.filter(order_product=articulos.id)
                                    if items_kits:
                                        for item_kit in items_kits:
                                        # Redusco Stock de los articulos Kits
                                            print("Productos del KIT", item_kit.product.id,item_kit.product.product_name, item_kit.quantity)

                                            product = Product.objects.get(id=item_kit.product.id)
                                            if product:
                                                #pesoarticulos += product.peso * item.quantity 
                                                product.stock = product.stock - item_kit.quantity
                                                product.save()
                                

                            
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
        #  SE RECALCULAN ....  descuentos = pedido.order_total_descuentos
        descuentos=0
        impuestos = pedido.order_total_impuestos
        comisiones = pedido.order_total_comisiones
        print("order_number",order_number)
        order_product = OrderProduct.objects.filter(order=id_pedido)
        print("items",order_product)
        if order_product:
            for i in order_product:
                subtotal += i.product_price * i.quantity
                #Recalculo el pese de los productos
                product = Product.objects.get(id=i.product_id)
                pesoarticulos += product.peso * i.quantity 
                descuentos = descuentos + (i.descuento_unitario * i.quantity)
                
            print("Total Descuento: ",descuentos)
            subtotal =  float(subtotal) - float(impuestos) - float(comisiones) - float(descuentos)
            subtotal = round(subtotal,2)
            print("Total Final: ",subtotal)
            print(" Restas imp, com, desc" , impuestos, comisiones, descuentos  )
            pedido = Order(
                pk = id_pedido,
                order_number = order_number,
                order_total = subtotal,
                created_at = pedido.created_at,
                envio= pedido.envio,
                fecha = pedido.fecha,
                user = pedido.user,
                payment = pedido.payment, 
                order_total_comisiones=  pedido.order_total_comisiones,
                order_total_descuentos=  descuentos,
                order_total_impuestos=  pedido.order_total_impuestos,
                origen_venta = pedido.origen_venta,
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
                dir_tipocorreo  = pedido.dir_tipocorreo,
                order_note  = pedido.order_note,
                fecha_tracking = pedido.fecha_tracking, 
                nro_tracking = pedido.nro_tracking,
           
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
            descuento_unitario = item_line.descuento_unitario

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
        print("descuento_unitario ", descuento_unitario)

        context = {
            'edit_order_number':order_number,
            'edit_item':item_line,
            'edit_quantity':quantity,
            'edit_item_subtotal': item_subtotal,
            'edit_precio':precio,
            'edit_descuento': descuento_unitario,
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

def panel_reporte_articulos_list(request):

    if validar_permisos(request,'REPORTE ARTICULOS'):

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
         # Fechas
        hoy = datetime.today()
        inicio_rango_6m = hoy - timedelta(days=30*6)  # Hace 6 meses
        inicio_mes_actual = hoy.replace(day=1)  # Inicio del mes actual

        # Ventas del mes actual
        ventas_mes_actual = (
            OrderProduct.objects.filter(
                order__fecha__gte=inicio_mes_actual,  # Solo el mes actual
                order__fecha__lte=hoy
            )
            .values('product__product_name', 'product__stock', 'product__stock_minimo')
            .annotate(
                total_ventas=Sum('quantity')  # Total de ventas del mes actual
            )
        )

        # Ventas de los últimos 6 meses (excluyendo el mes actual)
        ventas_6_meses = (
            OrderProduct.objects.filter(
                order__fecha__gte=inicio_rango_6m,  # Desde hace 6 meses
                order__fecha__lt=inicio_mes_actual  # Hasta antes del mes actual
            )
            .values('product__product_name', 'product__stock', 'product__stock_minimo')
            .annotate(
                promedio_ventas=Avg('quantity')  # Promedio de ventas de los últimos 6 meses
            )
        )

        # Combinar los resultados
        productos = {}
        for venta in ventas_mes_actual:
            productos[venta['product__product_name']] = {
                'stock': venta['product__stock'],
                'stock_minimo': venta['product__stock_minimo'],
                'total_mes_actual': venta['total_ventas'],
                'promedio_6_meses': 0,  # Valor por defecto si no hay datos en 6 meses
            }

        for venta in ventas_6_meses:
            if venta['product__product_name'] in productos:
                productos[venta['product__product_name']]['promedio_6_meses'] = venta['promedio_ventas']
            else:
                productos[venta['product__product_name']] = {
                    'stock': venta['product__stock'],
                    'stock_minimo': venta['product__stock_minimo'],
                    'total_mes_actual': 0,  # Valor por defecto si no hay ventas en el mes actual
                    'promedio_6_meses': venta['promedio_ventas'],
                }
                

        print(productos)
        
        context = {
            'permisousuario':permisousuario,
             'productos': productos
            #'fecha_desde':fecha_desde,
            #'fecha_hasta':fecha_hasta
            }
        

        
        return render (request,"panel/reporte_articulos.html",context)
    else:
        return render (request,"panel/login.html")

def panel_reporte_clientes_list(request):


    if validar_permisos(request,'REPORTE CLIENTES'):
        fecha_1 = request.POST.get("fecha_desde")
        fecha_2 = request.POST.get("fecha_hasta")     
        if not fecha_1 and not fecha_2 :
            fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
            dias = timedelta(days=90) 
            fecha_desde = fecha_hasta - dias
        else:
           
            fecha_desde = datetime.strptime(fecha_1, '%d/%m/%Y')
            fecha_hasta = datetime.strptime(fecha_2, '%d/%m/%Y')

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        clientes = Order.objects.filter(fecha__range=[fecha_desde,fecha_hasta]).values('last_name','first_name').annotate(total=
                     Round(
                Sum('order_total'),
                output_field=DecimalField(max_digits=12, decimal_places=2)),cantidad=Count('order_number')).order_by('last_name')
        
       

        context = {
            'permisousuario':permisousuario,
            'clientes':clientes,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta      
            }
        

        
        return render (request,"panel/reporte_clientes.html",context)
    else:
        return render (request,"panel/login.html")

def panel_cotiz_dolar_list(request):
    
    if validar_permisos(request,'DOLAR'):
        fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
        dias = timedelta(days=90) 
        fecha_desde = fecha_hasta - dias
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        dolar = ImportDolar.objects.filter(created_at__range=[fecha_desde,fecha_hasta],codigo='blue').order_by('-created_at')
        
        context = {
            'permisousuario':permisousuario,
            'dolar':dolar,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta
            }
    
        
        return render (request,"panel/lista_cotiz_dolar.html",context)
    else:
        return render (request,"panel/login.html")

def panel_cotiz_detalle(request,fecha=None):
    
    if validar_permisos(request,'DOLAR'):

       
        if request.method == "GET":
      
            fecha_dte = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d")
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            dolar = ImportDolar.objects.filter(created_at=fecha_dte).first()
        
            context = {
                'dolar':dolar,
                'permisousuario':permisousuario,
                'fecha_str':fecha_dte,
              
            }
            
            return render(request,'panel/dolar_cotiz.html',context) 

        if request.method=="POST":
           
            fecha=request.POST.get("fecha")
            venta=request.POST.get("venta")
            compra=request.POST.get("compra")
            
           

            venta = venta.replace(",", ".")
            compra = compra.replace(",", ".")
            suma = Decimal(venta) + Decimal(compra)
           
            promedio = suma / 2

            dolar = ImportDolar.objects.get(created_at=fecha)
            if dolar:
                    cot_dolar = ImportDolar(
                        id = dolar.id,
                        created_at=fecha,
                        codigo=dolar.codigo,
                        moneda=dolar.moneda,
                        nombre=dolar.nombre,
                        venta=venta,
                        compra=compra,
                        promedio = round(promedio,2),
                        fechaActualizacion= datetime.today()            )
                    cot_dolar.save()
            else:
                cot_dolar = ImportDolar(
                    created_at=fecha,
                    codigo=dolar.codigo,
                    moneda=dolar.moneda,
                    nombre=dolar.nombre,
                    venta=venta,
                    compra=compra,
                    promedio = round(promedio,2),
                    fechaActualizacion= datetime.today()         
                    )
                cot_dolar.save()

            return redirect('panel_cotiz_dolar_list')  

    else:
        return render (request,"panel/login.html")

def panel_costo_list(request):
        
    if validar_permisos(request,'COSTOS'):

        fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
        dias = timedelta(days=90) 
        fecha_desde = fecha_hasta - dias
       
        print(fecha_desde,fecha_hasta)
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        #
        
        costos = Costo.objects.filter(fecha_actualizacion__range=[fecha_desde,fecha_hasta]).order_by('-fecha_actualizacion')
        
        context = {
            'permisousuario':permisousuario,
            'costos':costos,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta
            }
        
        return render (request,"panel/lista_costos.html",context)
    else:
        return render (request,"panel/login.html")

def import_costo(request):
    
    if validar_permisos(request,'IMPORTAR COSTO'):
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
                        valor = sheet1.cell_value(rowNumber, 0).lower()
                        if valor != "producto": # Saco la primera file
                            try:
                                producto = sheet1.cell_value(rowNumber, 0)
                                costo = sheet1.cell_value(rowNumber, 1)
                                costo = float(costo)
                                
                            except ValueError:
                                cant_error += 1
                                error_str+="<br> El costo del articulo "+ str(producto)+" no es valido."
                                pass

                            tmp_producto = Product.objects.get(product_name=producto)
                            usuario = Account.objects.get(email=request.user)
                            if usuario:
                                if tmp_producto:
                                    print("Entré....")
                                    costos = Costo (
                                        producto=tmp_producto,
                                        costo=costo,
                                        fecha_actualizacion=datetime.today(),
                                        usuario=usuario,
                                        )
                                    costos.save()
                                    if tmp_producto:
                                        cant_ok=cant_ok+1
                                    else:
                                        cant_error=cant_error+1
                                        error_str = error_str + "<br> Error al grabar el costo del articulo: " + str(producto)
                            else:
                                cant_error=cant_error+1
                                error_str = error_str + "No se encontro al usuario " + str(request.user)
                    except OSError as err:
                        print("OS error:", err)
                        error_str = error_str + err + " ROW: " + str(rowNumber)
                        cant_error=cant_error+1
                        pass
                    except ValueError:
                        cant_error=cant_error+1
                        error_str = error_str  + " Error al convertir int -  ROW: " + str(rowNumber)  
                        
                        pass
                    except Exception as err:
                        error_str= error_str + producto
                        error_str= error_str + f" /n - Unexpected {err=}, {type(err)=}"
                        cant_error=cant_error+1
                        
                #Borro el archivo
                os.remove(archivo)
                
        context = {
                    'cant_ok':cant_ok,
                    'permisousuario':permisousuario,
                    'cant_error':cant_error,
                    'error_str':error_str,
                   
                            
                    }
        return render(request,'panel/importar_costo.html',context)
    else:
            return render (request,"panel/login.html")

def panel_costo_del(request,id_costo=None):
        
    if validar_permisos(request,'COSTOS'):

        fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
        dias = timedelta(days=90) 
        fecha_desde = fecha_hasta - dias
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        if id_costo:
            costos = Costo.objects.filter(id=id_costo).first()

            if costos:
                id = costos.id
                costos.delete()
                messages.success(request,"Costo eliminado con èxito")
            else:
                messages.error(request,"No se encoentro el costos")

        costos = Costo.objects.filter(fecha_actualizacion__range=[fecha_desde,fecha_hasta]).order_by('-fecha_actualizacion')
        
        context = {
            'permisousuario':permisousuario,
            'costos':costos,
            'fecha_desde':fecha_desde,
            'fecha_hasta':fecha_hasta
            }
        
        return render (request,"panel/lista_costos.html",context)
    else:
        return render (request,"panel/login.html")

def panel_costo_actualizar(request):
        
    if validar_permisos(request,'COSTOS'):

        fecha_hasta = datetime.today() + timedelta(days=1) # 2023-09-28
        dias = timedelta(days=90) 
        fecha_desde = fecha_hasta - dias
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        # Subquery para obtener la fecha de actualización más reciente para cada producto
        subquery = Costo.objects.filter(producto=OuterRef('producto')).order_by('-fecha_actualizacion')

        # Consulta principal que obtiene el costo más reciente para cada producto
        costos_recientes = Costo.objects.filter(
            fecha_actualizacion=Subquery(subquery.values('fecha_actualizacion')[:1])
        )

        # Si solo quieres una lista de costos recientes por producto
        for costo in costos_recientes:
            print(f"Producto: {costo.producto.product_name}, Costo más reciente: {costo.costo}")
            costo_producto = Product.objects.get(product_name=costo.producto.product_name)
            if costo_producto:
                costo_producto.costo_prod = costo.costo
                costo_producto.save()

        
        
        messages.success(request,"Costos actualizados.")
        return redirect('panel_costo_list')
        
    else:
        return render (request,"panel/login.html")

def panel_picking_list(request):
    
    if validar_permisos(request,'PICKING'):
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categoria = Category.objects.all().order_by('orden_picking')
        subcategoria = SubCategory.objects.all().order_by('orden_picking')         
        #ordern_picking = Orden_picking.objects.all()
        
        context = {
            'permisousuario':permisousuario,
            'categories':categoria,
            'subcategories':subcategoria #,
            #'ordern_picking':ordern_picking
            }
        

        
        return render (request,"panel/lista_picking.html",context)
    else:
        return render (request,"panel/login.html")

def category_list(request):
    categories = Category.objects.all().order_by('orden_picking')
    subcategories = SubCategory.objects.all().order_by('orden_picking')
    context = {
        'categories': categories,
        'subcategories': subcategories,
    }
    return render(request, 'categories/category_list.html', context)
#Funcion que ordena las categorias y subcategorias para listar en la hoja de pocking
def update_order(request):

    
    if request.method == 'POST':
        order_data = request.POST.get('order_data', None)
        if order_data:
            order_list = order_data.split(',')
            order_category = 0
            order_subcategory = 0
            
            for item in order_list:
                
                if 'categorie_' in item: 
                    category_id = item.split('_')[1]
                    print("Category:", category_id, order_category)
                    category = get_object_or_404(Category, id=category_id)
                    category.orden_picking = order_category
                    category.save()
                    order_category += 1
                elif 'subcategory_' in item:
                    subcategory_id = item.split('_')[1]
                    
                    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
                    subcategory.orden_picking = order_subcategory
                    subcategory.save()
                    order_subcategory += 1

            
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'failed'}, status=400)

def panel_lista_precios(request):
    
   
    if validar_permisos(request,'LISTA PRECIOS'):
       
        
        activos = request.POST.getlist("is_available[]")

        if activos:
            activos=True
            product_list = Product.objects.filter(is_available=True)
        else:
            activos=False
            product_list = Product.objects.all()

       

        # Obtener los valores de los márgenes con código MG1, MG2 y MG3
        margen1 = ConfiguracionParametros.objects.get(codigo='MG1')
        margen2 = ConfiguracionParametros.objects.get(codigo='MG2')
        margen3 = ConfiguracionParametros.objects.get(codigo='MG3')

        #COMISIONES DE VENTA  1 (Regular / Informal) 2 (Tienda Nube) 3 (Mercado Libre)
        comision1 = ConfiguracionParametros.objects.get(codigo='COM1')
        comision2 = ConfiguracionParametros.objects.get(codigo='COM2')
        comision3 = ConfiguracionParametros.objects.get(codigo='COM3')

        #COSTO FIJO x VENTA ML
        costo3_menor = ConfiguracionParametros.objects.get(codigo='CST3_1') # Monte menor a 12000
        costo3_mayor = ConfiguracionParametros.objects.get(codigo='CST3_2') # Monto mayor a 12000
        
        if not comision1:
            comision1=0
        if not comision2:
            comision2=0
        if not comision3:
            comision3=0
        if not costo3_menor:
            costo3_menor = 0
        if not costo3_mayor:
            costo3_mayor = 0
        
        category = request.POST.get("category")

        if category:
            if category=='0':
                try:
                    print("panel_lista_precios 1111")
                    # Verificar si los valores son porcentaje o valor monetario y anotarlos en el queryset
                    productos = Product.objects.filter(id__in=product_list).annotate(
                        # Cálculo del margen1 (costo + (costo * margen1 / 100))
                        precio_base=ExpressionWrapper(
                            F('costo_prod') * (float(margen1.valor) / 100) + F('costo_prod'),
                            output_field=FloatField()
                            ),
                        comision1_calculado=ExpressionWrapper(
                            F('price') * (float(comision1.valor) / 100),  # Precio de Venta Regular * Comision
                            output_field=FloatField()
                            ),
                        beneficio1_calculado=ExpressionWrapper(
                            F('price') - F('costo_prod') -F('comision1_calculado'),output_field=FloatField()
                            ),
                        # Cálculo del margen2 (precio_base + (precio_base * margen2 / 100))
                        precio_cal_tn=ExpressionWrapper(
                            F('precio_base') * (float(margen2.valor) / 100) + F('precio_base'),
                            output_field=FloatField()
                            ),
                        comision2_calculado=ExpressionWrapper(
                            F('precio_TN') * (float(comision2.valor) / 100),  # Precio de Venta Tienda Nube * Comision
                            output_field=FloatField()
                            ),
                        beneficio2_calculado=ExpressionWrapper(
                            F('precio_TN') - F('costo_prod') -F('comision2_calculado'),output_field=FloatField()
                            ),
                        # Cálculo del margen3 (precio_tn + (precio_tn * margen3 / 100))
                        precio_cal_ml=ExpressionWrapper(
                            F('precio_base') * (float(margen3.valor) / 100) + F('precio_base'),
                            output_field=FloatField()
                              ),
                        # Cálculo condicional de la comisión3 según el valor de precio_ML
                        comision3_calculado=ExpressionWrapper(
                            F('precio_ML') * (float(comision3.valor) / 100) + 
                            Case(
                                When(Q(precio_ML__gt=12000), then=Value(float(costo3_mayor.valor))),
                                default=Value(float(costo3_menor.valor)),
                                output_field=FloatField()
                            ),
                            output_field=FloatField()
                        ),
                        beneficio3_calculado=ExpressionWrapper(
                            F('precio_ML') - F('costo_prod') -F('comision3_calculado'),output_field=FloatField()
                            )
                        ).order_by('-stock')

                except ConfiguracionParametros.DoesNotExist:
                    # En caso de que no exista alguno de los márgenes, manejar la excepción.
                    print("panel_lista_precios 2222")
                    productos = Product.objects.all().order_by('product_name')
            else:
                
                try:
                    print("panel_lista_precios 3333")
                    # Verificar si los valores son porcentaje o valor monetario y anotarlos en el queryset
                    # Verificar si los valores son porcentaje o valor monetario y anotarlos en el queryset
                    productos = Product.objects.filter(id__in=product_list).annotate(
                        # Cálculo del margen1 (costo + (costo * margen1 / 100))
                        precio_base=ExpressionWrapper(
                            F('costo_prod') * (float(margen1.valor) / 100) + F('costo_prod'),
                            output_field=FloatField()
                            ),
                        comision1_calculado=ExpressionWrapper(
                            F('price') * (float(comision1.valor) / 100),  # Precio de Venta Regular * Comision
                            output_field=FloatField()
                            ),
                        beneficio1_calculado=ExpressionWrapper(
                            F('price') - F('costo_prod') -F('comision1_calculado'),output_field=FloatField()
                            ),
                        # Cálculo del margen2 (precio_base + (precio_base * margen2 / 100))
                        precio_cal_tn=ExpressionWrapper(
                            F('precio_base') * (float(margen2.valor) / 100) + F('precio_base'),
                            output_field=FloatField()
                            ),
                        comision2_calculado=ExpressionWrapper(
                            F('precio_TN') * (float(comision2.valor) / 100),  # Precio de Venta Tienda Nube * Comision
                            output_field=FloatField()
                            ),
                        beneficio2_calculado=ExpressionWrapper(
                            F('precio_TN') - F('costo_prod') -F('comision2_calculado'),output_field=FloatField()
                            ),
                        # Cálculo del margen3 (precio_tn + (precio_tn * margen3 / 100))
                        precio_cal_ml=ExpressionWrapper(
                            F('precio_base') * (float(margen3.valor) / 100) + F('precio_base'),
                            output_field=FloatField()
                              ),
                        # Cálculo condicional de la comisión3 según el valor de precio_ML
                        comision3_calculado=ExpressionWrapper(
                            F('precio_ML') * (float(comision3.valor) / 100) + 
                            Case(
                                When(Q(precio_ML__gt=12000), then=Value(float(costo3_mayor.valor))),
                                default=Value(float(costo3_menor.valor)),
                                output_field=FloatField()
                            ),
                            output_field=FloatField()
                        ),
                        beneficio3_calculado=ExpressionWrapper(
                            F('precio_ML') - F('costo_prod') -F('comision3_calculado'),output_field=FloatField()
                            )
                        ).order_by('-stck')


                except ConfiguracionParametros.DoesNotExist:
                    # En caso de que no exista alguno de los márgenes, manejar la excepción.
                    print("panel_lista_precios 4444")
                    productos = Product.objects.all().order_by('product_name')
        else:
            try:
                # Verificar si los valores son porcentaje o valor monetario y anotarlos en el queryset
                print("panel_lista_precios 5555")
                # Verificar si los valores son porcentaje o valor monetario y anotarlos en el queryset
                productos = Product.objects.filter(id__in=product_list).annotate(
                    # Cálculo del margen1 (costo + (costo * margen1 / 100))
                    precio_base=ExpressionWrapper(
                        F('costo_prod') * (float(margen1.valor) / 100) + F('costo_prod'),
                        output_field=FloatField()
                        ),
                    comision1_calculado=ExpressionWrapper(
                        F('price') * (float(comision1.valor) / 100),  # Precio de Venta Regular * Comision
                        output_field=FloatField()
                        ),
                    beneficio1_calculado=ExpressionWrapper(
                        F('price') - F('costo_prod') -F('comision1_calculado'),output_field=FloatField()
                        ),
                    # Cálculo del margen2 (precio_base + (precio_base * margen2 / 100))
                    precio_cal_tn=ExpressionWrapper(
                        F('precio_base') * (float(margen2.valor) / 100) + F('precio_base'),
                        output_field=FloatField()
                        ),
                    comision2_calculado=ExpressionWrapper(
                        F('precio_TN') * (float(comision2.valor) / 100),  # Precio de Venta Tienda Nube * Comision
                        output_field=FloatField()
                        ),
                    beneficio2_calculado=ExpressionWrapper(
                        F('precio_TN') - F('costo_prod') -F('comision2_calculado'),output_field=FloatField()
                        ),
                    # Cálculo del margen3 (precio_tn + (precio_tn * margen3 / 100))
                    precio_cal_ml=ExpressionWrapper(
                        F('precio_base') * (float(margen3.valor) / 100) + F('precio_base'),
                        output_field=FloatField()
                            ),
                    # Cálculo condicional de la comisión3 según el valor de precio_ML
                    comision3_calculado=ExpressionWrapper(
                        F('precio_ML') * (float(comision3.valor) / 100) + 
                        Case(
                            When(Q(precio_ML__gt=12000), then=Value(float(costo3_mayor.valor))),
                            default=Value(float(costo3_menor.valor)),
                            output_field=FloatField()
                        ),
                        output_field=FloatField()
                    ),
                    beneficio3_calculado=ExpressionWrapper(
                        F('precio_ML') - F('costo_prod') -F('comision3_calculado'),output_field=FloatField()
                        )
                    ).order_by('-stock')


            except ConfiguracionParametros.DoesNotExist:
                # En caso de que no exista alguno de los márgenes, manejar la excepción.
                print("panel_lista_precios 6666")
                productos = Product.objects.all().order_by('product_name')

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        categorias = Category.objects.all()
        subcategoria = []
        cantidad = productos.count()

        context = {
            'productos':productos,
            'permisousuario':permisousuario,
            'categorias':categorias,
            'subcategoria':subcategoria,
            'cantidad':cantidad,
            'activos':activos
        }
        
        return render(request,'panel/lista_de_precios.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_config_margen(request):
    
   
    if validar_permisos(request,'MARGENES'):
       
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        param = ConfiguracionParametros.objects.filter()
        context = {
            'permisousuario':permisousuario,
            'param':param
        }
       
        return render(request,'panel/lista_parametros.html',context) 
    else:
        return render (request,"panel/login.html")

def panel_margen_edit(request,id_param=None):

    if validar_permisos(request,'MARGENES'):

        if request.method == 'GET':
       
            param = ConfiguracionParametros.objects.filter(id=id_param).first()
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            
            context = {
                'permisousuario':permisousuario,
                'param':param
            }
        
            return render(request,'panel/parametros_edit.html',context)

        if request.method == 'POST':

            id_param = request.POST["idparam"]
            valor = request.POST["valor"]

            if id_param:
                if valor:
                    param = ConfiguracionParametros.objects.get(id=id_param)
                    param.valor = valor
                    param.save()
            
            param = ConfiguracionParametros.objects.filter()
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            
            context = {
                'permisousuario':permisousuario,
                'param':param
            }

            return render(request,'panel/lista_parametros.html',context) 
    else:
        return render (request,"panel/login.html")

# INI SERVICIOS SOAP OCA ******************
def costo_envio_view(request):
    resultado = None
    if request.method == 'POST':
        peso_total = request.POST.get('peso_total')
        volumen_total = request.POST.get('volumen_total')
        cp_origen = request.POST.get('cp_origen')
        cp_destino = request.POST.get('cp_destino')
        cant_paquetes = request.POST.get('cant_paquetes')
        valor_declarado = request.POST.get('valor_declarado')
        cuit = request.POST.get('cuit')
        operativa = request.POST.get('operativa')

        # Llamar a la función consultar_costo_envio
        try:
            resultado = consultar_costo_envio(peso_total, volumen_total, cp_origen, cp_destino, cant_paquetes, valor_declarado, cuit, operativa)
        except Exception as e:
            resultado = {'error': str(e)}

    return render(request, 'panel/consulta_costo_envio.html', {'resultado': resultado})

def costo_envio_by_cart(request,cp_destino):
        resultado = None


        print("costo_envio_by_cart")
        print("obteniendo tocken Correo Argentino...")
        token = refesh_token_correo_argentino()
        print("Token:")
        print("obteniendo customer_id Correo Argentino")
        customer_id= get_customer_correo_arg()
        print("customer_id:",customer_id)

      
        
        total= 0
        peso = 0
        cart_items = CartItem.objects.filter(user=request.user)
        for cart_item in cart_items:
            total += (cart_item.product.peso * cart_item.quantity)
            

        peso = total/1000
       
 
        # Llamar a la función consultar_costo_envio
        try:
            print("llamando servicios OCA....")
            #OCA
            resultado_ed = oca_consultar_costo_envio_by_cart(peso, cp_destino,1) #Envio Domicilio
            resultado_rs = oca_consultar_costo_envio_by_cart(peso, cp_destino,2) # Retira Sucursal
            #Correo Argentino
            print("llamando servicios CA ....")
            
            resultado_ed_ca = ca_consultar_costo_envio_by_cart(peso,cp_destino,'D',token,customer_id) #Envio a Domicilio
            resultado_rs_ca = ca_consultar_costo_envio_by_cart(peso,cp_destino,'S',token,customer_id) #Sucursal

            print("**** Envio Domicilio  ***** CA ")
            precio_ed_ca_clasico=0
            precio_ed_ca_expreso=0
            # Iterar sobre los productos
            for producto in resultado_ed_ca['productos']:
                if producto['productType'] == 'CP':
                    precio_ed_ca_clasico = float("{0:.2f}".format(producto['price']))
                elif producto['productType'] == 'EP':
                    precio_ed_ca_expreso = float("{0:.2f}".format(producto['price']))

            # Imprimir los resultados
            precio_rs_ca_clasico=0
            precio_rs_ca_expreso=0
            for resultado in resultado_rs_ca['productos']:
                if resultado['productType'] == 'CP':
                    precio_rs_ca_clasico = float("{0:.2f}".format((float)(resultado['price'])))
                if resultado['productType'] == 'EP':
                    precio_rs_ca_expreso = float("{0:.2f}".format((float)(resultado['price'])))

            if not resultado_ed:
                precio_ed_oca = "A definir"
                plazo_entrega_ed_oca = 0
            else:
                plazo_entrega_ed_oca = resultado_ed['PlazoEntrega']
                precio_ed_oca = float("{0:.2f}".format((float)(resultado_ed['Total'])))
            
            if not resultado_rs:
                precio_rs_oca = "A definir"
                plazo_entrega_rs_oca = 0
            else:
                plazo_entrega_rs_oca = resultado_rs['PlazoEntrega']
                precio_rs_oca = float("{0:.2f}".format((float)(resultado_rs['Total'])))
            

            if not precio_ed_ca_clasico:
                precio_ed_ca_clasico = "A definir"
            if not precio_ed_ca_expreso:
                precio_ed_ca_expreso = "A definir"
            if not precio_rs_ca_clasico:
                precio_rs_ca_clasico = "A definir"
            if not precio_rs_ca_expreso:
                precio_rs_ca_expreso = "A definir"

            resultado = {
                
                'Total_ed': precio_ed_oca,
                'Plazo_ed': plazo_entrega_ed_oca,
                'Total_rs': precio_rs_oca,
                'Plazo_rs': plazo_entrega_rs_oca,
                'precio_ed_ca_clasico':precio_ed_ca_clasico,
                'precio_ed_ca_expreso':precio_ed_ca_expreso,
                'precio_rs_ca_clasico':precio_rs_ca_clasico,
                'precio_rs_ca_expreso':precio_rs_ca_expreso

            }

        except Exception as e:

            precio_ed_oca = "A definir"
            plazo_entrega_ed_oca = "A definir"
            precio_rs_oca = "A definir"
            plazo_entrega_rs_oca = "A definir"
            precio_ed_ca_clasico = "A definir"
            precio_ed_ca_expreso = "A definir"
            precio_rs_ca_clasico = "A definir"
            precio_rs_ca_expreso = "A definir"

            resultado = {
                
                'Total_ed': precio_ed_oca,
                'Plazo_ed': plazo_entrega_ed_oca,
                'Total_rs': precio_rs_oca,
                'Plazo_rs': plazo_entrega_rs_oca,
                'precio_ed_ca_clasico':precio_ed_ca_clasico,
                'precio_ed_ca_expreso':precio_ed_ca_expreso,
                'precio_rs_ca_clasico':precio_rs_ca_clasico,
                'precio_rs_ca_expreso':precio_rs_ca_expreso

            }

        #print(resultado)
        return JsonResponse(resultado, safe=False)
       
def consultar_suc_by_cp(request):
    
    centros_info = None
    dir_id_2="0"
    print("View: consultar_suc_by_cp")

    if request.method == 'POST':
        cp_destino = request.POST.get('cp_destino')
        dir_id_2 = request.POST.get('dir_id_3')
       

        # Llamar a la función consultar_sucursal_bycp
        if cp_destino:
            try:
               
                centros_info = consultar_sucursal_bycp(cp_destino,dir_id_2)
                

            except Exception as e:
                centros_info = {'error': f"Hubo un problema al consultar la sucursal: {str(e)}"}
        else:
            centros_info = {'error': 'El código postal no puede estar vacío.'}
    
    return render(request, 'accounts/edit_direcciones.html', {'centros_info': centros_info})
# FIN SERVICIOS SOAP OCA ******************

# INI SERVICIOS CORREO ARGENTINO ******************
def obtener_token_correo_argentino():


    # Reemplaza con tu usuario y contraseña
    usuario = settings.USER_CORREO_ARG
    contrasena = settings.PASS_CORREO_ARG

    # URL para solicitar el token
    url = "https://api.correoargentino.com.ar/micorreo/v1/token"

    try:
        # Realiza la solicitud POST con autenticación básica
        response = requests.post(url, auth=HTTPBasicAuth(usuario, contrasena))

        # Verifica si la solicitud fue exitosa (código de estado 200)
        if response.status_code == 200:
            # Extrae el token del JSON de respuesta
            token = response.json().get("token")
            fecha_venc= response.json().get("expire")
            #print("Tocken Correo Arg:", token, fecha_venc)

            return token, fecha_venc
        else:
            #print("Error al obtener el token:", response.status_code, response.text)
            return None, None
    except requests.RequestException as e:
        print("Error en la solicitud:", e)
        return None, None
## LLAMAR A ESTA FUNCION PARA OBTENER EL TOKEN
#token = refesh_token_correo_argentino()
def refesh_token_correo_argentino():

    print("View: refesh_token_correo_argentino")
    access_token=''
    customerId=settings.CUSTOMERID_CORREO_ARG
    # 1 Valido si tengo guardado el token y es valido (fecha)
        
    user_id= settings.USER_CORREO_ARG
    authorization_code = meli_params.objects.filter(userid=user_id).first()
    
    if not authorization_code:
        #Grabo el token 
        token, last_update = obtener_token_correo_argentino()
        #print("Token: ", token)
        if token:
            print("Grabando datos del token en la tabla....")
            rs_access_token = meli_params.objects.get(client_id=customerId)
            if rs_access_token:
                rs_access_token.code = '',
                rs_access_token.access_token=token,
                rs_access_token.token_type= 'Bearer ',
                rs_access_token.userid= settings.USER_CORREO_ARG,  #USER Y PASS LIFCHE
                rs_access_token.refresh_token = '',
                rs_access_token.last_update = last_update
                rs_access_token.save()
    
            return token
        else:
            print("No token found - refesh_token_correo_argentino")
    else:
        
        fecha_venc = authorization_code.last_update
        fecha_venc = str(fecha_venc) if not isinstance(fecha_venc, str) else fecha_venc
        
        try:
            expiration_datetime = datetime.fromisoformat(fecha_venc)
            ahora = datetime.now()

            
            if expiration_datetime > ahora:
                print("Token valido, no es necesario refrescarlo")
                return authorization_code.access_token
            else:
                token, last_update = obtener_token_correo_argentino()
                customerId = settings.CUSTOMERID_CORREO_ARG
                print("Tengo Tocken y Customer")

                # Obtener el objeto de access_token de meli_params con el client_id correspondiente
                access_token = meli_params.objects.get(client_id=customerId)

                # Si el token existe, actualizamos sus atributos
                if access_token:
                    access_token.access_token = token
                    access_token.token_type = 'Bearer'
                    access_token.userid = settings.USER_CORREO_ARG
                    access_token.last_update = last_update

                    # Guardar el objeto actualizado
                    access_token.save()
                        
                return token
        except ValueError:
            print("Error: La fecha de vencimiento no está en un formato ISO 8601 válido.")
            
def get_serv_customer_id_correo_argentino(token):


    url = "https://api.correoargentino.com.ar/micorreo/v1/users/validate"

    customerId=''
    payload = json.dumps({
    "email": settings.EMAIL_USER_CORREO_ARG ,
    "password": settings.EMAIL_PASS_CORREO_ARG
    })

    
    headers = {
    'Authorization': 'Bearer ' + str(token),
    'Content-Type': 'application/json'  # ,
    #v'Cookie': '7326f8819575d808a8a5b3a67c3616d6=209c792f93d7aa5fb08eff96537d0086'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
    
        customerId = response.json().get("customerId")
   
    return customerId

def get_customer_correo_arg():

    customer_id=settings.CUSTOMERID_CORREO_ARG
    #user_id= settings.USER_CORREO_ARG
    #authorization_code = meli_params.objects.filter(userid=user_id).first()
    #if not authorization_code:
    #    token = refesh_token_correo_argentino()
    #    customer_id = get_serv_customer_id_correo_argentino(token)
    #else:
    #    customer_id = authorization_code.client_id
    
    return customer_id

def marcar_como_leida(request, alerta_id):

    print("PASE POR MARCAR_COMO_LEIDA")

    # Obtener y marcar la alerta como leída
    alerta = get_object_or_404(Alerta, id=alerta_id, usuario=request.user)
    alerta.leido = True
    alerta.save()

     # Obtener permisos y alertas no leídas
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
    alertas = Alerta.objects.filter(usuario=request.user, leido=False)



    # Retornar *querysets* directamente usando su representación como listas
    return JsonResponse({
        'success': True,
        'permisousuario': list(permisousuario.values()),  # Serializar queryset
        'alertas': list(alertas.values()),               # Serializar queryset
        'cant_alertas': alertas.count(),
    })

def compras_detalle_producto_reporte(request):

    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
      
    # 1. Obtener todos los productos vendidos, incluidos los productos dentro de los kits.
    productos_vendidos = (
        OrderProduct.objects.filter(
            order__status__in=['Accepted', 'Completed', 'Cancelled', 'Cobrado', 'Entregado']
        )
        .values(
            'product_id',  # ID del producto
            'product__product_name',  # Nombre del producto
            'product__stock'  # Stock actual del producto
        )
        .annotate(
            total_cantidad_vendida=Sum('quantity')  # Sumar cantidad vendida por producto
        )
    )
    #print("Productos Vendidos:", productos_vendidos)

    # 2. Obtener todas las compras realizadas de productos individuales.
    compras = (
        ComprasDet.objects.filter(id_compra_enc__estado=2)  # Filtrar compras recibidas
        .values(
            'producto__id_product_id',  # ID del producto
            'producto__id_product__product_name',  # Nombre del producto
            'producto__id_product__stock'  # Stock actual del producto
        )
        .annotate(
            total_cantidad_comprada=Sum('cantidad')  # Sumar cantidad comprada por producto
        )
    )
    #print("Compras:", compras)

    # 3. Preparar los datos finales de productos.
    productos_comprados = {}
    
    for compra in compras:
        producto_id = compra['producto__id_product_id']
        productos_comprados[producto_id] = {
            'nombre': compra['producto__id_product__product_name'],
            'stock_actual': compra['producto__id_product__stock'],
            'total_cantidad_comprada': compra['total_cantidad_comprada'],
            'total_cantidad_vendida': 0,  # Inicialmente 0, se sumarán las ventas más tarde
        }
    #print("Productos Comprados Iniciales:", productos_comprados)

    # 4. Actualizar las ventas de productos en los productos_comprados.
    for venta in productos_vendidos:
        producto_id = venta['product_id']
        if producto_id in productos_comprados:
            productos_comprados[producto_id]['total_cantidad_vendida'] = venta['total_cantidad_vendida']
    #print("Productos con Ventas Actualizadas:", productos_comprados)

    # 5. Calcular la cantidad vendida para productos dentro de los kits.
    for venta in OrderProductKitItem.objects.filter(
        order_product__order__status__in=['Accepted', 'Completed', 'Cancelled', 'Cobrado', 'Entregado']
    ):
        producto_id = venta.product.id  # Producto dentro del kit
        cantidad_vendida_kit = venta.quantity * venta.order_product.quantity  # Cantidad vendida dentro del kit
       
        if producto_id in productos_comprados:
            productos_comprados[producto_id]['total_cantidad_vendida'] += cantidad_vendida_kit
    #print("Productos con Ventas de Kits Actualizadas:", productos_comprados)

    # 6. Calcular la diferencia final entre lo comprado, lo vendido y el stock actual.
    for producto_id, datos in productos_comprados.items():
        datos['diferencia_final'] = (
            datos['total_cantidad_comprada'] - datos['total_cantidad_vendida'] - datos['stock_actual']
        )
    #print("Productos con Diferencia Final Calculada:", productos_comprados)

    # 7. Convertir los productos_comprados en una lista para enviarla a la plantilla.
    productos_finales = [
        {
            'producto_id': producto_id,
            'nombre': datos['nombre'],
            'stock_actual': datos['stock_actual'],
            'total_cantidad_comprada': datos['total_cantidad_comprada'],
            'total_cantidad_vendida': datos['total_cantidad_vendida'],
            'diferencia_final': datos['diferencia_final'],
        }
        for producto_id, datos in productos_comprados.items()
    ]
    #print("Productos Finales para Plantilla:", productos_finales)

    context = {
        'permisousuario':permisousuario,
            'productos': productos_finales
        }
    

    # Renderizar los datos en una plantilla HTML
    return render(request, 'panel/reporte_compras.html', context)