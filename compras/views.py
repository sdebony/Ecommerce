
from django.shortcuts import render,  get_object_or_404,redirect
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import AccountPermition
from panel.models import ImportDolar
from contabilidad.models import Cuentas,Movimientos,Operaciones
from store.models import Costo
from category.models import Category,SubCategory
from compras.models import CompraDolar,Proveedores,ProveedorArticulos,Marcas,UnidadMedida,ComprasEnc,ComprasDet
from panel.views import validar_permisos
from slugify import slugify
from django.contrib import messages

from orders.models import Order
from store.models import Product
from django.db.models import Subquery, OuterRef, ExpressionWrapper, F, FloatField,Value,CharField
from django.db.models.functions import Coalesce,Round
from django.http import JsonResponse, HttpResponseBadRequest
import json
import math


from django.conf import settings




from datetime import datetime

from urllib.parse import unquote
# DOLARES
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
            movimientos_agrupados = Movimientos.objects.filter(fecha__gte=fecha_solicitud, movimiento=1, idcierre=0, cuenta_id=cuenta_id).annotate(
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

#PROVEEDORES
def proveedores_list(request):
    
    if validar_permisos(request,'PROVEEDORES'):

        #Maestro de proveedores
        proveedores = Proveedores.objects.filter().all().order_by('nombre')
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        context = {
            'proveedores': proveedores,
            'permisousuario': permisousuario,
            }
        return render(request,'compras/lista_proveedores.html',context)


    else:
        return render(request,'panel/login.html',)

def proveedores_add(request):
    
    if validar_permisos(request,'PROVEEDORES'):

        #Maestro de proveedores
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       
        if request.method == 'POST':
            
            idproveedor= request.POST["idproveedor"]
            nombre= request.POST["nombre"]
            direccion= request.POST["direccion"]
            contacto= request.POST["contacto"]
            telefono1= request.POST["telefono1"]
            telefono2= request.POST["telefono2"]
            email= request.POST["email"]
            web= request.POST["web"]
            facebook= request.POST["facebook"]
            instragram= request.POST["instragram"]
            
            if idproveedor:
                proveedor = Proveedores.objects.get(id=idproveedor)
                proveedor.id = idproveedor
                proveedor.nombre = nombre
                proveedor.direccion = direccion
                proveedor.contacto = contacto
                proveedor.telefono1 = telefono1
                proveedor.telefono2 = telefono2
                proveedor.email = email
                proveedor.web = web
                proveedor.facebook = facebook
                proveedor.instragram = instragram
                proveedor.save()
            else:
                proveedor = Proveedores.objects.create(
                    nombre=nombre,
                    direccion=direccion,
                    contacto = contacto,
                    telefono1=telefono1,
                    telefono2=telefono2,
                    email=email,
                    web=web,
                    facebook=facebook,
                    instragram=instragram
                    )
                proveedor.save()
       
            proveedores = Proveedores.objects.filter().all().order_by('nombre')

            context = {
                'proveedores': proveedores,
                'permisousuario': permisousuario,
            }
            return render(request,'compras/lista_proveedores.html',context)

        else:

            context = {
                'permisousuario': permisousuario,
                }
            return render(request,'compras/proveedores.html',context)


    else:
        return render(request,'panel/login.html',)

def proveedores_update(request,prov_id=None):
    
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

    if validar_permisos(request,'PROVEEDORES'):

        #Maestro de proveedores
        if request.method == 'POST':
            print("Update Proveedor:", prov_id)
            idproveedor= prov_id
            nombre= request.POST["nombre"]
            direccion= request.POST["direccion"]
            contacto= request.POST["contacto"]
            telefono1= request.POST["telefono1"]
            telefono2= request.POST["telefono2"]
            email= request.POST["email"]
            web= request.POST["web"]
            facebook= request.POST["facebook"]
            instragram= request.POST["instragram"]
           
            if idproveedor:
                proveedor = Proveedores.objects.get(id=idproveedor)
                proveedor.id = idproveedor
                proveedor.nombre = nombre
                proveedor.direccion = direccion
                proveedor.contacto = contacto
                proveedor.telefono1 = telefono1
                proveedor.telefono2 = telefono2
                proveedor.email = email
                proveedor.web = web
                proveedor.facebook = facebook
                proveedor.instragram = instragram
                proveedor.save()
           
            proveedores = Proveedores.objects.filter().all().order_by('nombre')

            context = {
                'proveedores': proveedores,
                'permisousuario': permisousuario,
            }
            return render(request,'compras/lista_proveedores.html',context)

        else:
            print("Update Proveedor:", prov_id)
            proveedores = Proveedores.objects.filter(id=prov_id).first()


            context = {
                'proveedores': proveedores,
                'permisousuario': permisousuario,
                }
            return render(request,'compras/proveedores.html',context)


    else:
        return render(request,'panel/login.html',)

def proveedores_del(request,prov_id=None):
    
    if validar_permisos(request,'PROVEEDORES'):

        #Maestro de proveedores
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
       

        proveedor = Proveedores.objects.get(id=prov_id)
        proveedor.delete()
   
    
        proveedores = Proveedores.objects.filter().all().order_by('nombre')

        context = {
            'proveedores': proveedores,
            'permisousuario': permisousuario,
        }
        return render(request,'compras/lista_proveedores.html',context)

    else:
        return render(request,'panel/login.html',)

#PROVEEDORES ARTICULOS
def proveedor_list_articulos(request,prov_id=None):

    if validar_permisos(request,'PROVEEDORES'):
        #Maestro de articulos
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        if request.method == 'GET':

            if prov_id:
                articulos = ProveedorArticulos.objects.filter(proveedor_id=prov_id).order_by('nombre_articulo')
                proveedor = Proveedores.objects.filter(id=prov_id).first()
                if proveedor:
                    proveedor_nombre = proveedor.nombre
            else:
                articulos = [] 
                proveedor_nombre=""               

            context = {
                'articulos': articulos,
                'proveedor_nombre':proveedor_nombre,
                'proveedor_id':prov_id,
                'permisousuario': permisousuario,
            }
            return render(request,'compras/lista_precios_proveedor.html',context)
    else:
      return render(request,'panel/login.html',)

#Comparacion costos por articulo de cada proveedor
def proveedor_check_articulos(request):

    if validar_permisos(request,'PROVEEDORES'):
        

        if request.method == 'GET':
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

            # Subquery para obtener el proveedor con el menor precio_por_unidad
            subquery_proveedor_articulos = ProveedorArticulos.objects.filter(
                id_product=OuterRef('pk'),
                precio_por_unidad__gt=1  # Condición para que el precio por unidad sea mayor a 1
            ).order_by('precio_por_unidad')

            # Hacer la consulta principal con los datos del proveedor y el precio por unidad
            productos = Product.objects.annotate(
                proveedor=Coalesce(
                    Subquery(subquery_proveedor_articulos.values('proveedor__nombre')[:1]), 
                    Value(None, output_field=CharField())
                ),
                nombre_articulo=Coalesce(
                    Subquery(subquery_proveedor_articulos.values('nombre_articulo')[:1]), 
                    Value(None, output_field=CharField())
                ),
                precio_por_unidad=Coalesce(
                    Subquery(subquery_proveedor_articulos.values('precio_por_unidad')[:1]), 
                    Value(0, output_field=FloatField())
                )
            ).values('product_name', 'stock','costo_prod', 'proveedor', 'nombre_articulo', 'precio_por_unidad')

            

            context = {
                'productos': productos,
                'permisousuario': permisousuario,
            }
            return render(request,'compras/lista_comparecion_proveedores.html',context)

        if request.method == 'POST':

            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

            # Subquery para obtener el proveedor con el menor precio_por_unidad
            subquery_proveedor_articulos = ProveedorArticulos.objects.filter(
                id_product=OuterRef('pk'),
                precio_por_unidad__gt=1  # Condición para que el precio por unidad sea mayor a 1
            ).order_by('precio_por_unidad')

            # Hacer la consulta principal con los datos del proveedor y el precio por unidad
            productos = Product.objects.annotate(
                proveedor=Coalesce(
                    Subquery(subquery_proveedor_articulos.values('proveedor__nombre')[:1]), 
                    Value(None, output_field=CharField())
                ),
                nombre_articulo=Coalesce(
                    Subquery(subquery_proveedor_articulos.values('nombre_articulo')[:1]), 
                    Value(None, output_field=CharField())
                ),
                precio_por_unidad=Coalesce(
                    Subquery(subquery_proveedor_articulos.values('precio_por_unidad')[:1]), 
                    Value(0, output_field=FloatField())
                )
            ).values('product_name', 'costo_prod', 'proveedor', 'nombre_articulo', 'precio_por_unidad')

            #GUARDO EN LA TABLA DE IMPORT COSTO PARA SER ACTUALIZADA DESDE EL MODULO COSTOS DONDE ACTUALIZA LA TABLA PRODUCTO
            if productos:
                for prod in productos:
                    if prod['precio_por_unidad'] > 0:
                        prod_slug = slugify(prod['product_name']).lower()
                        product = Product.objects.filter(slug=prod_slug).first()

                        costos = Costo (
                            producto=product,
                            costo=prod['precio_por_unidad'],
                            fecha_actualizacion=datetime.today(),
                            usuario=request.user,
                        )
                        print(prod['product_name'],prod['precio_por_unidad'])
                        costos.save()
            
            context = {
                'productos': productos,
                'permisousuario': permisousuario,
            }
            return render(request,'compras/lista_comparecion_proveedores.html',context)


    else:
      return render(request,'panel/login.html',)
        
def proveedor_articulo(request,prov_id=None,codigo_prod_prov=None):

    if validar_permisos(request,'PROVEEDORES'):
        print("Edit articulo")
        id_nuevo_prod = 0

        if request.method == 'GET':
            producto = ProveedorArticulos.objects.filter(codigo_prod_prov=codigo_prod_prov,proveedor=prov_id).first()
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            marcas = Marcas.objects.filter().all()
            unidades = UnidadMedida.objects.filter().all()
            proveedor = Proveedores.objects.filter(id=prov_id).first()
            if proveedor:
                proveedor_nombre = proveedor.nombre
            else:
                proveedor_nombre = "Proveedor no encontrado"
            
            print(marcas)
            context = {
                'producto': producto,
                'proveedor_nombre':proveedor_nombre,
                'proveedor_id':prov_id,
                'marcas':marcas,
                'unidades':unidades,
                'permisousuario': permisousuario,
            }
            return render(request,'compras/producto_proveedor.html',context)
        
        if request.method == 'POST':
            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            marcas = Marcas.objects.all()
            unidades = UnidadMedida.objects.all()

            action = request.POST.get('action') 

            idprod= request.POST["idprod"]
            prov_id= request.POST["idprov"]
            codigo_prod_prov= request.POST["codigo_prod_prov"]
            nombre_articulo= request.POST["nombre_articulo"]
            marca= request.POST["marca"]
            descripcion= request.POST["descripcion"]
            unidad_medida= request.POST["unidad_medida"]
            cantidad_unidad_medida= request.POST["cantidad_unidad_medida"]
            precio_compra= request.POST["precio_compra"]
            precio_por_unidad= request.POST["precio_por_unidad"]
            peso_por_unidad= request.POST["peso_por_unidad"]
            estado= request.POST.getlist("estado[]")
            imagen= request.POST["imagen"]
            link= request.POST["link"]
           
            obj_marca = Marcas.objects.filter(marca=marca).first()
            obj_unidad_medida = UnidadMedida.objects.filter(codigo=unidad_medida).first()
            obj_proveedor = Proveedores.objects.filter(id=prov_id).first()

            if not imagen:
                imagen = "3fb9e34af7fc5e657276aa22f57cdac0/none.gif"
            
            if estado:
                estado = True
            else:
                estado = False

            product_slug_name= slugify(nombre_articulo).lower()

            if action=="create":

                category_slug=settings.DEF_CATEGORY_ADD_PROD
                subcategory_slug=settings.DEF_SUBCATEGORY_ADD_PROD
                #Genero un producto propio en base a los datos del producto del proveedor
                category = Category.objects.filter(slug=category_slug).first()
                subcategory = SubCategory.objects.filter(category=category,sub_category_slug=subcategory_slug).first()
                producto = Product.objects.filter(slug=product_slug_name).first()
                if not producto:
                    registar_prodcuto = Product(
                        product_name=nombre_articulo,
                        slug=slugify(nombre_articulo).lower(),
                        description=descripcion,
                        price=0,
                        images=imagen,
                        imgfile =imagen,
                        stock=0,
                        is_available=True,
                        category=category,
                        subcategory = subcategory,
                        created_date =datetime.today(), 
                        modified_date=datetime.today(),
                        is_popular=False,
                        peso=peso_por_unidad
                        )
                    registar_prodcuto.save()
                    if registar_prodcuto:
                        id_nuevo_prod = registar_prodcuto.id
                    print("Se creo un nuevo articulo",id_nuevo_prod)
               
               

            if idprod:
                articulo = ProveedorArticulos.objects.get(id=idprod)
                articulo.id = idprod
                articulo.codigo_prod_prov = codigo_prod_prov
                articulo.nombre_articulo = nombre_articulo
                articulo.marca = obj_marca
                articulo.descripcion = descripcion
                articulo.proveedor = obj_proveedor
                articulo.unidad_medida = obj_unidad_medida
                articulo.cantidad_unidad_medida = cantidad_unidad_medida
                articulo.precio_compra = precio_compra
                articulo.precio_por_unidad = precio_por_unidad
                articulo.peso_por_unidad = peso_por_unidad
                articulo.estado = estado
                articulo.imagen = imagen
                articulo.link = link
                articulo.fecha_actualizacion = datetime.today()
                articulo.id_product = Product.objects.filter(slug=product_slug_name).first()
                articulo.save()
                id_nuevo_prod = articulo.id
               

            else:
                articulo = ProveedorArticulos(
                    codigo_prod_prov=codigo_prod_prov,
                    nombre_articulo=nombre_articulo,
                    marca=obj_marca,
                    descripcion=descripcion,
                    unidad_medida=obj_unidad_medida,
                    proveedor = obj_proveedor,
                    cantidad_unidad_medida=cantidad_unidad_medida,
                    precio_compra=precio_compra,
                    precio_por_unidad=precio_por_unidad,
                    peso_por_unidad=peso_por_unidad,
                    estado=estado,
                    imagen=imagen,
                    link=link,
                    fecha_actualizacion = datetime.today(),
                    id_product = Product.objects.filter(slug=product_slug_name).first()
                    )
                articulo.save()
                id_nuevo_prod = articulo.id  
                         
            if prov_id:
                articulos = ProveedorArticulos.objects.filter(proveedor_id=prov_id).order_by('nombre_articulo')
                proveedor = Proveedores.objects.filter(id=prov_id).first()
                if proveedor:
                    proveedor_nombre = proveedor.nombre
            else:
                articulos = [] 
                proveedor_nombre=""               

            context = {
                'articulos': articulos,
                'proveedor_nombre':proveedor_nombre,
                'proveedor_id':prov_id,
                'permisousuario': permisousuario,
            }
            return render(request,'compras/lista_precios_proveedor.html',context)

            
    else:
        return render(request,'panel/login.html',)

# Vista para renderizar el formulario y manejar el POST
def vincular_articulo(request):

    if request.method == 'POST':
       
        proveedor_id = request.POST.get('proveedor')
        producto_proveedor_id = request.POST.get('producto')
        producto_propio_id = request.POST.get('producto_propio')

       
        proveedor = Proveedores.objects.get(id=proveedor_id)
        producto = Product.objects.get(id=producto_propio_id)

        # Crear el nuevo artículo del proveedor
    
        vinc_articulo = ProveedorArticulos.objects.get(id=producto_proveedor_id)
        if vinc_articulo:
            vinc_articulo.proveedor=proveedor
            vinc_articulo.id_product=producto
            vinc_articulo.save()

       

    # Obtener proveedores para el formulario
    proveedores = Proveedores.objects.all()
    productos = Product.objects.all()
    permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
         
    
    return render(request, 'compras/vincular_articulo.html', {'proveedores': proveedores,'productos': productos,'permisousuario':permisousuario,})

# Vista para devolver productos del proveedor seleccionado (usada por AJAX)
def get_productos(request, proveedor_id):
    
    if validar_permisos(request,'PROVEEDORES'):
        productos = ProveedorArticulos.objects.filter(proveedor_id=proveedor_id)
        productos_data = [{'id': prod.id, 'nombre_articulo': prod.nombre_articulo, 'precio_por_unidad': prod.precio_por_unidad, 'marca': prod.marca.marca} for prod in productos]
        return JsonResponse({'productos': productos_data})
    else:
        productos = []
        productos_data = []
        return JsonResponse({'productos': productos_data})

#Ordenes de Compra
def generar_orden_compra(request):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        proveedores = Proveedores.objects.all()

        return render(request, 'compras/orden_de_compra.html', {
            'permisousuario': permisousuario,
            'proveedores':proveedores,
        })

    else:
        return render(request,'panel/login.html',)

#Graba los datos de las Ordenes de compra
def procesar_datos(request):
  
    if request.method == 'POST':
        try:
            # Cargar datos JSON del cuerpo de la solicitud
            datos = json.loads(request.body)

            # Obtener los datos del encabezado
            encabezado = datos.get('encabezado', {})
            detalles = datos.get('detalles', [])

            # Aquí puedes procesar los datos, por ejemplo, guardar en la base de datos
            # Ejemplo: print(encabezado) y print(detalles) en consola
            #print("Encabezado:", encabezado)
            #print("Detalles:", detalles)
            

            if encabezado:
                id_prov = encabezado['id_proveedor'] #Para Update del txt

                if id_prov == '0':
                    id_prov = encabezado['proveedor'] #Para New del Select
                
                

                proveedor = Proveedores.objects.filter(id=id_prov).first()
                #print("proveedor",proveedor)
                    
                monto=encabezado['subtotal']
                #Sub Total: $ 7.331,00 1ra vez
               
                print("Sub Total:", monto)
                subtotal = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                print("subtotal",subtotal)
                
                monto=encabezado['envio']
                costoenvio = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                print("envio",costoenvio)

                monto=encabezado['descuentos']
                descuentos = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                print("descuentos",descuentos)

                monto=encabezado['total']
                total = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                print("total",total)

                fecha_str = encabezado['fecha']
                fecha_compra = datetime.strptime(fecha_str, '%d/%m/%Y')
                print("fecha",fecha_compra)

                observaciones = encabezado['observaciones']

                id_oc = encabezado['id_oc']
                print(str(id_oc))

                if proveedor:
                    try:
                        if int(id_oc) > 0:
                            # Actualizar la orden de compra
                            proveedor_rs = Proveedores.objects.filter(id=id_prov).first()

                            orden_compra = ComprasEnc.objects.filter(id=id_oc).first()
                            orden_compra.proveedor = proveedor_rs
                            orden_compra.sub_total = subtotal
                            orden_compra.costoenvio = costoenvio
                            orden_compra.descuento = descuentos
                            orden_compra.total = total
                            orden_compra.fecha_compra = fecha_compra
                            orden_compra.observacion = observaciones
                            orden_compra.save()
                            print("orden de compra actualizada", orden_compra.id)

                        else:
                            orden_compra = ComprasEnc.objects.create(
                                fecha_compra=fecha_compra,
                                observacion=observaciones,
                                sub_total=subtotal,
                                costoenvio=costoenvio,
                                descuento=descuentos,
                                total=total,
                                estado=0, #Nuevo
                                proveedor=proveedor,
                            )
                            orden_compra.save()
                            #print("Compra creada:", orden_compra.id)
                    except Exception as e:
                        print("Error al crear la compra:", e)
                        
                    if orden_compra:
                        #Elimino el detalle de la compra para agregar nuevamente
                        detalle_oc = ComprasDet.objects.filter(id_compra_enc=id_oc)
                        if detalle_oc.exists():
                            for det in detalle_oc:
                                det.delete()
                           

                        for detalle in detalles:
                            #articulo_prov = detalle['producto']
                            idproducto = detalle['idproducto']
                            print(idproducto)
                            producto = ProveedorArticulos.objects.filter(id=idproducto).first()

                            cant=detalle['cantidad']
                            cantidad = float(cant.replace('$', '').replace(',', '').replace(',', '.'))
                            print("cantidad",cantidad)

                            monto=detalle['precio']
                            precio = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                            print("precio",precio)

                            monto=detalle['subtotal']
                            subtotal = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                            print("subtotal",subtotal)

                            monto=detalle['descuento']
                            descuento = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                            print("descuento",descuento)

                            monto=detalle['total']
                            total = float(monto.replace('$', '').replace(',', '').replace(',', '.'))
                           #print("total",total)

                           

                            detalle_compra = ComprasDet.objects.create(
                                id_compra_enc=orden_compra,
                                producto=producto,
                                cantidad=cantidad,
                                precio_prv=precio,
                                sub_total=subtotal,
                                descuento=descuento,
                                total=total,
                                )
                            detalle_compra.save()
                            #print("detalle de compra creado:", detalle_compra.id)

                            
            
            # Responder con éxito
            return JsonResponse({'status': 'success'})

        except json.JSONDecodeError:
            return HttpResponseBadRequest('Error al decodificar JSON')

    return HttpResponseBadRequest('Método no permitido')
#Lista de Ordenes de Compra a Proveedores
def oc_list(request):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        oc_compras = ComprasEnc.objects.all()

        return render(request, 'compras/lista_ordenes_compra_prov.html', {
            'permisousuario': permisousuario,
            'oc_compras':oc_compras,
        })

    else:
        return render(request,'panel/login.html',)

def oc_detalle(request,id_oc=None):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')

        oc_enc_compras = ComprasEnc.objects.filter(id=id_oc).first()
        if oc_enc_compras:
            proveedor_id = oc_enc_compras.proveedor.id
            oc_detalle_compras = ComprasDet.objects.filter(id_compra_enc=id_oc)
            productos_prov = ProveedorArticulos.objects.filter(proveedor_id=proveedor_id)
        else:
            oc_detalle_compras = None
            oc_enc_compras=None
            productos_prov=None


        return render(request, 'compras/orden_de_compra.html', {
            'permisousuario': permisousuario,
            'productos_prov':productos_prov,
            'oc_enc_compras': oc_enc_compras,
            'oc_detalle_compras':oc_detalle_compras,
        })

    else:
        return render(request,'panel/login.html',)

def oc_detalle_ver(request,id_oc=None):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        print("Ver orden de Compra")
        oc_enc_compras = ComprasEnc.objects.filter(id=id_oc).first()
        if oc_enc_compras:
            proveedor_id = oc_enc_compras.proveedor.id
            oc_detalle_compras = ComprasDet.objects.filter(id_compra_enc=id_oc)
            productos_prov = ProveedorArticulos.objects.filter(proveedor_id=proveedor_id)
        else:
            oc_detalle_compras = None
            oc_enc_compras=None
            productos_prov=None


        return render(request, 'compras/orden_de_compra_ver.html', {
            'permisousuario': permisousuario,
            'productos_prov':productos_prov,
            'oc_enc_compras': oc_enc_compras,
            'oc_detalle_compras':oc_detalle_compras,
        })

    else:
        return render(request,'panel/login.html',)

def oc_delete(request,id_oc=None):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA

        
        oc_enc_compras = ComprasEnc.objects.filter(id=id_oc).first()
        if oc_enc_compras:   
            oc_detalle_compras = ComprasDet.objects.filter(id_compra_enc=id_oc)
            if oc_detalle_compras.exists():
                for det in oc_detalle_compras:
                    det.delete()
            oc_enc_compras.delete()
            messages.success(request, 'Se ha eliminado la orden de compra del proveedor.')
        return redirect('oc_list')

    else:
        return render(request,'panel/login.html',)

def oc_registrar_pago(request,id_oc=None):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA

        if request.method == 'GET':

            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            oc_enc_compras = ComprasEnc.objects.filter(id=id_oc).first()
            cuentas = Cuentas.objects.all()
            
            fecha_actual = datetime.now()
            if oc_enc_compras:
                proveedor = oc_enc_compras.proveedor

            return render(request, 'compras/registrar_pago_orden_compra.html', {
                'permisousuario': permisousuario,
                'oc_enc_compras': oc_enc_compras,
                'cuentas': cuentas,
                'fecha_actual': fecha_actual,
                'proveedor': proveedor,
            })

        if request.method == 'POST':

            id_oc = request.POST.get('id_oc')
            fecha_pago = request.POST.get('fecha')
            cuenta_pago = request.POST.get('cuenta')
            cliente = request.POST.get('cliente')
            total = request.POST.get('total')

            print(id_oc,fecha_pago,cuenta_pago,cliente,total)
            # GRABAR TRX EN MOVIMIENTOS
            current_date = fecha_pago
            oper = Operaciones.objects.filter(codigo="EGR").first() #Ingresos
            cuentas= Cuentas.objects.get(id=cuenta_pago)
        
            if float(total)>0:
                total = float(total) * -1

            
            cliente = "Proveedor:" + str(cliente)
            trx = Movimientos(
                    fecha =current_date,
                    cliente = cliente,
                    movimiento = oper,
                    cuenta = cuentas,
                    monto=total,
                    observaciones = "Pago Orden Compra: " + str(id_oc),
                    idtransferencia = 0,
                    ordernumber = None,
            )
            trx.save()
            id_trx = trx.id
            print("id_trx",id_trx)


            if id_trx > 0:
                oc_enc_compras = ComprasEnc.objects.get(id=id_oc)
                if oc_enc_compras:
                    oc_enc_compras.id_pago = id_trx
                    oc_enc_compras.estado = 1 # 0-Nuevo  1-Pagado 2-Entregado
                    oc_enc_compras.save()


            return redirect('oc_list')
           
    
    else:
        return render(request,'panel/login.html',)

def oc_recibir(request,id_oc=None):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA


        if request.method == 'GET':

            permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
            print("Ver orden de Compra")
            oc_enc_compras = ComprasEnc.objects.filter(id=id_oc).first()
            if oc_enc_compras:
                proveedor_id = oc_enc_compras.proveedor.id
                oc_detalle_compras = ComprasDet.objects.filter(id_compra_enc=id_oc)
                productos_prov = ProveedorArticulos.objects.filter(proveedor_id=proveedor_id)
            else:
                oc_detalle_compras = None
                oc_enc_compras=None
                productos_prov=None


            return render(request, 'compras/orden_de_compra_recibir.html', {
                'permisousuario': permisousuario,
                'productos_prov':productos_prov,
                'oc_enc_compras': oc_enc_compras,
                'oc_detalle_compras':oc_detalle_compras,
            })
        
        if request.method == 'POST':
            # Obtén los datos del formulario
            
            idproductos = request.POST.getlist('idproducto[]')
            costos = request.POST.getlist('costo[]')
            cantidades_recibidas = request.POST.getlist('cantidad_recibida[]')
            envio = request.POST.get('envio')
            descuento = request.POST.get('descuento')
            total_recibido=0

            otros_costo = float(envio) - float(descuento)
            for idproducto, costo, cantidad_recibida in zip(idproductos, costos, cantidades_recibidas):
                total_recibido = total_recibido + float(cantidad_recibida)
            
            if total_recibido > 0:
                otros_costo = float(otros_costo) / float(total_recibido)
                otros_costo = math.ceil(otros_costo)

            # Puedes procesar los datos como necesites
            for idproducto, costo, cantidad_recibida in zip(idproductos, costos, cantidades_recibidas):
                
                
                costo = costo.replace('$', '').replace(',', '')
                
                costo_float = float(costo) + float(otros_costo) #Agrego costo Flete
                costo_float = math.ceil(costo_float)
                #print(f'idproducto:', {idproducto},)
                #print(f'costo:', {costo_float},)
                #print(f'stock:', {cantidad_recibida},)
                product = Product.objects.get(id=idproducto)
                if product:
                        #Valido si el producto tiene aun stock
                        if product.stock > 0:
                            #Actualizo el Costo del producto Total Actual Stock x Costo + cant_recib x nuevo costo
                            total_costo = (product.stock * product.costo_prod) + (int(cantidad_recibida) * costo_float )
                            total_stock = product.stock + int(cantidad_recibida)
                            product.costo_prod = total_costo / total_stock
                            #Actualizo el stock del producto
                            product.stock = total_stock
                            print("Nuevo Costo: ", product.costo_prod, " Nuevo Stock: ",total_stock)
                            product.save()
                            
                        else:
                            product.id = idproducto
                            product.stock += float(cantidad_recibida)
                            product.costo_prod = float(costo_float)
                            product.save()

            #Cambia a estado Finalizada OC_ENC
            oc_enc_compras = ComprasEnc.objects.get(id=id_oc)
            if oc_enc_compras:
                oc_enc_compras.id = id_oc
                oc_enc_compras.estado = 2 #Finalizado
                oc_enc_compras.save()
                      

            return redirect('oc_list')
    
 
    else:
        return render(request,'panel/login.html',)

def oc_anula_recepcion(request,id_oc=None):

    if validar_permisos(request,'ORDENES DE COMPRA'):  #ORDEN DE COMPRA

            # Obtén los datos del formulario
            
        if id_oc:   

            oc_enc_compras = ComprasEnc.objects.get(id=id_oc)
            if oc_enc_compras:
                oc_enc_compras.id = id_oc
                oc_enc_compras.estado = 1 #Pagado
                oc_enc_compras.save()
                #print("OC:",id_oc)
                oc_det_compras = ComprasDet.objects.filter(id_compra_enc=id_oc)
                if oc_det_compras:
                    for item in oc_det_compras:
                        producto = Product.objects.get(id=item.producto.id_product.id)
                        nueva_cantidad = producto.stock - item.cantidad
                    
                        if nueva_cantidad > 0:
                            #Total Actual
                            totalcosto = producto.stock * producto.costo_prod # Esto es el total actual sin descontar
                            total_oc_anula = item.cantidad * item.precio_prv
                            totalcosto = totalcosto - total_oc_anula
                            totalcostonvo = totalcosto /  nueva_cantidad #Descuento la anulacion
                            producto.stock = producto.stock - item.cantidad
                            producto.costo_prod = totalcostonvo
                            producto.save()
                        else:
                            producto.costo_prod = 0
                            producto.stock = producto.stock - item.cantidad
                            producto.save() 

            return redirect('oc_list')
    
 
    else:
        return render(request,'panel/login.html',)


