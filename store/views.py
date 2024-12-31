from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery, ProductKit,ProductKitEnc
from category.models import Category,SubCategory
from carts.models import CartItem,CartItemKit,Cart
from django.db.models import Q,Value
from django.db.models.functions import Concat
from store.models import ReglaDescuento
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct


from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt


def store(request, category_slug=None,subcategory_slug=None):
   
    categories = None
    products = None
    product_count=0
    category_id = 0
    subcategy_id = 0
    subcategories=[]
    categories = []
    category_name=""
    sub_category_name = ""
  
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    print("Store....")
    if 'Mobile' in user_agent:
        resolucion=settings.STORE_TEMPLATE_MOBILE
    else:
        resolucion=settings.STORE_TEMPLATE  #DEFAULT = PC Normal.  Tipo 2    
       
    if category_slug != None:
        if subcategory_slug != None and "todos" not in subcategory_slug.lower():
            print("Subcategoria seleccionada")
            print("TEST TEST TEST TEST TEST TEST TEST TEST ")
            categories = get_object_or_404(Category.objects.order_by("orden"), slug=category_slug)
            subcategory = get_object_or_404(SubCategory, sub_category_slug=subcategory_slug) #Para el Query de productos
            subcategories = SubCategory.objects.filter(category=categories)
            products = Product.objects.filter(category=categories,subcategory=subcategory, is_available=True).order_by('product_name')            
            product_count = products.count()
            paginator = Paginator(products, settings.PRODUCT_PAGE_STORE)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
        
            category_id = categories.id
            subcategy_id = subcategory.id

            if subcategory:
                sub_category_name = subcategory.subcategory_name
            else:
                sub_category_name = ""
        else:
            if subcategory_slug == None:
                print("Sin seleccion subcategoria ")

                categories = get_object_or_404(Category.objects.order_by("orden"), slug=category_slug)
                subcategory = SubCategory.objects.filter(category=categories).exclude(subcategory_name__iexact="todos").order_by('orden').first() #Para el Query de productos
                subcategories = SubCategory.objects.filter(category=categories)
                print("Primera subcategoria:",subcategory)
                sub_category_name = subcategory.subcategory_name
                print("subcategoria:",sub_category_name)
                products = Product.objects.filter(category=categories,subcategory=subcategory, is_available=True).order_by('product_name')           
                #products = Product.objects.filter(category=categories, is_available=True).order_by('product_name').annotate(desc= Concat(f'product_name',Value('*')))
            elif  "todos" in subcategory_slug.lower():
                print("Todos")
                categories = get_object_or_404(Category.objects.order_by("orden"), slug=category_slug)
                #subcategories = get_object_or_404(SubCategory, category=categories)
                subcategories = SubCategory.objects.filter(category=categories)
                products = Product.objects.filter(category=categories, is_available=True).order_by('product_name')   


            paginator = Paginator(products, settings.PRODUCT_PAGE_STORE)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()
            category_id = categories.id
            subcategy_id = 0
    else:
        subcategories=[]
        category_slug=settings.DEF_CATEGORY
        subcategory_slug=settings.DEF_SUBCATEGORY

        print("Categoria Default:", category_slug)
        print("Subcategoria Default:", subcategory_slug)
        
        categories = get_object_or_404(Category.objects.order_by("orden"), slug=category_slug)

        subcat = get_object_or_404(SubCategory, category=categories,sub_category_slug=subcategory_slug)
        subcategories = SubCategory.objects.filter(category=categories)
        products = Product.objects.filter(category=categories,subcategory=subcat, is_available=True).order_by('product_name')
        
        product_count = products.count()


        paginator = Paginator(products, settings.PRODUCT_PAGE_STORE)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        category_id = 0
        subcategy_id = 0
        

    if categories:
        category_name = categories.category_name
        category_slug = categories.slug
    else:
        category_name = ""

    
    # Obtenemos todas las reglas de descuento activas
    #reglas_descuento = ReglaDescuento.objects.filter(activo=True)

    # Recorrer los productos y agregar el campo 'tiene_descuento'
    for producto in paged_products:
        # Inicializamos el campo tiene_descuento como False
        tiene_descuento = False
        

        # Verificamos si alguna regla de descuento es aplicable al producto
        mejor_descuento = obtener_mejor_descuento(producto, 1)

        # Extraer los valores de promo y tipo_descuento
        descuento = mejor_descuento["descuento"]
        porcenteje_descuento = mejor_descuento["porcenteje_descuento"]
        if descuento > 0:
            tiene_descuento = True
        else:
            tiene_descuento = False
        
        # Ahora puedes usar promo y tipo_descuento como variables independientes
        print(f"descuento: {descuento}, Tiene descuento: {tiene_descuento}, porcenteje_descuento:,{porcenteje_descuento}")
        
        # Agregar el campo 'tiene_descuento' al producto
        producto.tiene_descuento = tiene_descuento
        producto.descuento = descuento
        producto.porcenteje_descuento = porcenteje_descuento
    
    context = {
        'products': paged_products,
        'product_count': product_count,
        'category_id':category_id,
        'subcategory_id':subcategy_id,
        'category_name':category_name,
        'category_slug':category_slug,
        'sub_category_name':sub_category_name,
        'subcategories':subcategories,
        'resolucion':resolucion
    }

   
    
    if resolucion == "1": #Celular
        return render(request, 'store/store.html', context)
    elif resolucion =="2":   #PC Normal
        return render(request,'store/full_store.html', context)
    elif resolucion =="3":  #Celular Test Nuew Store
        return render(request,'store/new_store2.html', context)
    else:   #Default para test mariano 
        return render(request, 'store/new_store.html', context)

def product_detail(request, category_slug, product_slug):

    
    
    print("product_detail: User: ")
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        user=request.user
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
            user=None
    else:
        user=None
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    
    cartitemkit=[]
    if not user:
        print("Not User, in_car:",in_cart)
        cartitem = CartItem.objects.filter(product=single_product.id,cart=in_cart).first()
    else:
        print("User:",user)
        cartitem = CartItem.objects.filter(product=single_product.id,user=user).first()
    if cartitem:
        print("cartitem product",cartitem)
        if user:
            cartitemkit = CartItemKit.objects.filter(cart=cartitem,user=user)
            print(cartitemkit)
        else:
            print("No User")
            cartitemkit = CartItemKit.objects.filter(cart=cartitem)
            print(cartitemkit)

    
    kit=[]
    productos_kit=[]
    if single_product.es_kit:
        try:
            print("es kit:",single_product)
            kit = ProductKitEnc.objects.get(productokit=single_product)
            if kit:
                productos_kit = ProductKit.objects.filter(productokit=kit)
        except:
            pass

   

    context = {
        'single_product': single_product,
        'in_cart'       : in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'kit':kit,
        'productos_kit': productos_kit,
        'cartitemkit':cartitemkit,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):

    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    print("Store....")
    if 'Mobile' in user_agent:
        resolucion=settings.STORE_TEMPLATE_MOBILE
    else:
        resolucion=settings.STORE_TEMPLATE  #DEFAULT = PC Normal.  Tipo 2    


    print("*****store***",resolucion)    

    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    
    else:
        products = Product.objects.filter(is_available=True).order_by('product_name')
        product_count = products.count()
            
    
    for producto in products:
        # Inicializamos el campo tiene_descuento como False
        tiene_descuento = False
        

        # Verificamos si alguna regla de descuento es aplicable al producto
        mejor_descuento = obtener_mejor_descuento(producto, 1)

        # Extraer los valores de promo y tipo_descuento
        descuento = mejor_descuento["descuento"]
        porcenteje_descuento = mejor_descuento["porcenteje_descuento"]
        if descuento > 0:
            tiene_descuento = True
        else:
            tiene_descuento = False
        
        # Ahora puedes usar promo y tipo_descuento como variables independientes
        print(f"descuento: {descuento}, Tiene descuento: {tiene_descuento}, porcenteje_descuento:,{porcenteje_descuento}")
        
        # Agregar el campo 'tiene_descuento' al producto
        producto.tiene_descuento = tiene_descuento
        producto.descuento = descuento
        producto.porcenteje_descuento = porcenteje_descuento
   

    
    context = {
        'products': products,
        'product_count': product_count,
        'category_id':0,
        'subcategory_id':0,
        'resolucion':resolucion
    }

    if resolucion == "1": #Celular
        return render(request, 'store/store.html', context)
    elif resolucion =="2":   #PC Normal
        return render(request,'store/full_store.html', context)
    elif resolucion =="3":  #Celular Test Nuew Store
        return render(request,'store/new_store2.html', context)
    else:   #Default para test mariano 
        return render(request, 'store/new_store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)

def condiciones (request):

    return render (request,"includes/como_comprar.html")
 
def obtener_mejor_descuento(producto, cantidad):
    
    ahora = datetime.now()

    # Filtrar reglas activas
    reglas = ReglaDescuento.objects.filter(
        activo=True,
        fecha_inicio__lte=ahora,
        fecha_fin__gte=ahora,
    )

    mejor_descuento = None
    mejor_valor = 0
    porcenteje_descuento = 0

    # Evaluar todas las reglas activas
    for regla in reglas:
        # Convertir tipo_descuento a mayúsculas para comparación consistente
        tipo_descuento = regla.tipo_descuento.upper()

        # Variables para el descuento
        descuento_actual = 0
        
        # Descuento por porcentaje
        if tipo_descuento == 'PORCENTAJE':
            if regla.productos.filter(id=producto.id).exists():
                # Si la regla aplica a este producto específico
                if regla.cantidad_minima <= int(cantidad):
                    porcenteje_descuento = regla.valor_descuento
                    descuento_actual = (producto.price * int(cantidad)) * (regla.valor_descuento / 100)
                    
            elif regla.categoria.exists() and regla.subcategoria.exists():
                # Si la regla aplica a la combinación de categorías y subcategorías
                if producto.category in regla.categoria.all() and producto.subcategory in regla.subcategoria.all():
                    if regla.cantidad_minima <= int(cantidad):
                        porcenteje_descuento = regla.valor_descuento
                        descuento_actual = (producto.price * int(cantidad)) * (regla.valor_descuento / 100)
                        
            elif regla.productos.exists() and (regla.categoria.exists() or regla.subcategoria.exists()):
                # Si tiene productos específicos y además una categoría/subcategoría asociada
                if producto.category in regla.categoria.all() or producto.subcategory in regla.subcategoria.all():
                    if regla.cantidad_minima <= int(cantidad):
                        porcenteje_descuento = regla.valor_descuento
                        descuento_actual = (producto.price * int(cantidad)) * (regla.valor_descuento / 100)
                        
            elif not regla.productos.exists() and (regla.categoria.exists() or regla.subcategoria.exists()):
                # Si no tiene productos pero tiene categoría o subcategoría asociada
                if producto.category in regla.categoria.all() or producto.subcategory in regla.subcategoria.all():
                    if regla.cantidad_minima <= int(cantidad):
                        porcenteje_descuento = regla.valor_descuento
                        descuento_actual = (producto.price * int(cantidad)) * (regla.valor_descuento / 100)


        # Descuento fijo
        elif tipo_descuento == 'FIJO':
            if regla.productos.filter(id=producto.id).exists():
                # Si la regla aplica a este producto específico
                if regla.cantidad_minima <= int(cantidad):
                    descuento_actual = regla.valor_descuento
                    
            elif regla.categoria.exists() and regla.subcategoria.exists():
                # Si la regla aplica a la combinación de categorías y subcategorías
                if producto.category in regla.categoria.all() and producto.subcategory in regla.subcategoria.all():
                    if regla.cantidad_minima <= int(cantidad):
                        descuento_actual = regla.valor_descuento
                        
            elif regla.productos.exists() and (regla.categoria.exists() or regla.subcategoria.exists()):
                # Si tiene productos específicos y además una categoría/subcategoría asociada
                if producto.category in regla.categoria.all() or producto.subcategory in regla.subcategoria.all():
                    if regla.cantidad_minima <= int(cantidad):
                        descuento_actual = regla.valor_descuento                    
            elif not regla.productos.exists() and (regla.categoria.exists() or regla.subcategoria.exists()):
                # Si no tiene productos pero tiene categoría o subcategoría asociada
                if producto.category in regla.categoria.all() or producto.subcategory in regla.subcategoria.all():
                    if regla.cantidad_minima <= int(cantidad):
                        descuento_actual = regla.valor_descuento
                        
        # Si encontramos un mejor descuento, lo asignamos
       
        if descuento_actual > mejor_valor:
            mejor_valor = descuento_actual
            mejor_descuento = regla
        
    

    # Retornar el mejor descuento encontrado
    return {
        "descuento": round(mejor_valor,2),
        "porcenteje_descuento":porcenteje_descuento,
        "tipo_descuento": mejor_descuento.tipo_descuento if mejor_descuento else None,
        "regla_descuento": mejor_descuento.nombre if mejor_descuento else None,
        "id_regla_descuento": mejor_descuento.id if mejor_descuento else None,
    }
