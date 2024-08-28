
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import AccountPermition
from panel.models import ImportDolar
from contabilidad.models import Cuentas,Movimientos
from compras.models import CompraDolar
from orders.models import Order

from django.db.models import Subquery, OuterRef, ExpressionWrapper, F, FloatField
from django.db.models.functions import Coalesce,Round

from django.db.models import Sum




from datetime import datetime

from urllib.parse import unquote
# Create your views here.
def compras_home(request):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='COMPRAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    if accesousuario.codigo.codigo =='COMPRAS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        cuentas = Cuentas.objects.filter().all()
        fecha = datetime.today()

      


        context = {
            'permisousuario':permisousuario,
            'cuentas':cuentas,
            'fecha': fecha,
           
        }
       
        return render(request,'compras/compras.html',context) 

    return render(request,'panel/login.html',)

def compras_save(request):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='COMPRAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    if accesousuario.codigo.codigo =='COMPRAS':
        
        if request.method == 'POST':
            
            monto= request.POST["monto"]
            fecha= request.POST["fecha"]
            cuenta= request.POST.get("cuenta")
                    
            #idcompra= request.POST["idcompra"]
            print(cuenta,"<-- Cuenta param")
            compra_moneda = []
            cuentas = Cuentas.objects.filter(id=cuenta).first()
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            if cuentas:
                print("cuenta model:",cuentas)
                compra_moneda = CompraDolar.objects.filter(cuenta=cuentas, fecha = fecha).first()
                if compra_moneda:
                    compra_moneda = CompraDolar(
                        id = compra_moneda.id,
                        fecha=fecha,
                        cuenta=cuentas,
                        monto= monto)
                    compra_moneda.save()
                    print("compra_moneda Update")
                else:
                    compra_moneda = CompraDolar(
                        fecha=fecha,
                        cuenta=cuentas,
                        monto= monto)
                    compra_moneda.save()
                    print("compra_moneda Nueva")


            sol_compras = CompraDolar.objects.filter().all().order_by('-fecha')


            context = {
                'permisousuario': permisousuario,
                'sol_compras':sol_compras,
            }
                
            return render(request,'compras/lista_compra_dolar.html',context) 

    return render(request,'panel/login.html',)

def compras_usd_detalle(request,sol_id=None):

    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='COMPRAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    if accesousuario.codigo.codigo =='COMPRAS':
        
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        
        movimientos_agrupados = []
       
        solicitudes = CompraDolar.objects.get(id=sol_id)
        if solicitudes:
            str_fecha = solicitudes.fecha
            fecha_solicitud = datetime.strptime(str(str_fecha), '%Y-%m-%d %H:%M:%S')
            fecha_solicitud = fecha_solicitud.strftime('%Y-%m-%d')
            cuenta_id = solicitudes.cuenta.id
            cuenta_nombre = solicitudes.cuenta.nombre

            # **************************************
            # C O B R A D O 
            # **************************************

            # Subconsulta para obtener el promedio de ImportDolar correspondiente a la fecha del movimiento
            subquery_promedio = ImportDolar.objects.filter(
                created_at__date=OuterRef('fecha')
            ).values('promedio')[:1]

            # Queryset para obtener las operaciones con la información adicional del promedio y el cálculo de Total_USD
            movimientos_agrupados = Movimientos.objects.filter(fecha__gte=fecha_solicitud, idtransferencia=0, idcierre=0, cuenta_id=cuenta_id).annotate(
                promedio=Subquery(subquery_promedio, output_field=FloatField()),
                Total_USD=Round(ExpressionWrapper(
                    F('monto') / Coalesce(Subquery(subquery_promedio), 1.0),
                    output_field=FloatField()),2)
            )


            pedidos_agrupados = Order.objects.filter(status='New', cuenta=cuenta_id).annotate(
                promedio=Subquery(subquery_promedio, output_field=FloatField()),
                Total_USD=Round(ExpressionWrapper(
                    F('order_total') / Coalesce(Subquery(subquery_promedio), 1.0),
                    output_field=FloatField()),2)
            )
           
        print(movimientos_agrupados)
        print(pedidos_agrupados)
           
        context = {
            'permisousuario': permisousuario,
            'resultado':movimientos_agrupados,
            'pedidos_agrupados':pedidos_agrupados,
            'cuenta_nombre':cuenta_nombre
            
        }
            
        return render(request,'compras/compras_detalle_mov.html',context) 

    return render(request,'panel/login.html',)

def compras_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='COMPRAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    if accesousuario.codigo.codigo =='COMPRAS':
        
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        sol_compras = CompraDolar.objects.filter().all().order_by('-fecha')


        context = {
            'permisousuario': permisousuario,
            'sol_compras':sol_compras,
        }
            
        return render(request,'compras/lista_compra_dolar.html',context) 

    return render(request,'panel/login.html',)

def compras_close(request,sol_id=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='COMPRAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    if accesousuario.codigo.codigo =='COMPRAS':
        
        sol_compras = []
        sol_compras = CompraDolar.objects.filter().all().order_by('-fecha')
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        solicitudes = CompraDolar.objects.get(id=sol_id)
        if solicitudes:
            compra_moneda = CompraDolar(
                id = sol_id,
                fecha = solicitudes.fecha,
                monto = solicitudes.monto,
                cuenta = solicitudes.cuenta,
                estado=True)
            compra_moneda.save()
            print("compra_moneda Update")


        context = {
            'permisousuario': permisousuario,
            'sol_compras':sol_compras,
        }
            
        return render(request,'compras/lista_compra_dolar.html',context) 

    return render(request,'panel/login.html',)

def compras_usd_delete(request,sol_id=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='COMPRAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    if accesousuario.codigo.codigo =='COMPRAS':
        
        sol_compras = []
        sol_compras = CompraDolar.objects.filter().all().order_by('-fecha')
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        compra_moneda = CompraDolar.objects.get(id=sol_id)
        if compra_moneda:
            compra_moneda.delete()

  


        context = {
            'permisousuario': permisousuario,
            'sol_compras':sol_compras,
        }
            
        return render(request,'compras/lista_compra_dolar.html',context) 

    return render(request,'panel/login.html',)