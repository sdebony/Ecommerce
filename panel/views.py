from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import AccountPermition
from django.core.exceptions import ObjectDoesNotExist

from store.models import Product,Variation
from orders.models import Order, OrderProduct
from category.models import Category

from datetime import datetime
from slugify import slugify

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
        
        permisousuario = AccountPermition.objects.filter(user=request.user)
        context = {
            'permisousuario':permisousuario,
            }
        print("Acceso Panel")
        return render (request,"panel/base.html",context)
    print('Sin modulo PANEL')
    return render(request,'dashboard',)

def panel_product_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CATALOGO')
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CATALOGO':

        permisousuario = AccountPermition.objects.filter(user=request.user)

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
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
    
    if accesousuario.codigo.codigo =='PRODUCTO':

        permisousuario = AccountPermition.objects.filter(user=request.user)
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
       
def panel_pedidos_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='ORDENES')
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='ORDENES':

        permisousuario = AccountPermition.objects.filter(user=request.user)

        ordenes = Order.objects.all().order_by('-created_at')
        cantidad = ordenes.count()

        context = {
            'ordenes':ordenes,
            'permisousuario':permisousuario,
            'cantidad':cantidad,
        }
        print(ordenes)
        return render(request,'panel/lista_pedidos.html',context) 

    return render(request,'panel/login.html',)

def panel_productos_variantes(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='PRODUCTO')
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
            accesousuario =  get_object_or_404(AccountPermition, user=request.user.id, codigo__codigo ='PRODUCTO',modo_editar=True)  #Permiso de Editar   
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
            permisousuario = AccountPermition.objects.filter(user=request.user)
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
                        is_available=True,
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
            accesousuario =  get_object_or_404(AccountPermition, user=request.user.id, codigo__codigo ='PRODUCTO',modo_editar=True)  #Permiso de Editar   
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