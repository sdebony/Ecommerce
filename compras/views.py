
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import AccountPermition
from store.models import Product

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
    
      
        context = {
            'permisousuario':permisousuario,
           
        }
       
        return render(request,'compras/compras.html',context) 

    return render(request,'panel/login.html',)

def search_proveedor_lookup(request,keyword=None):

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
        
    }
    return render(request, 'compras/proveedor_lookup.html' , context)
