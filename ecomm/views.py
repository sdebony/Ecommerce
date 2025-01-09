from django.shortcuts import render
from store.models import Product, ReviewRating
from django.contrib import messages

from django.conf import settings

def home(request):

    from store.views import obtener_mejor_descuento
    
    #products = Product.objects.all().filter(is_available=True).order_by('product_name')[:20]
    products = Product.objects.filter(is_available=True,is_popular=True).order_by('product_name')[:settings.POPULAR_PRODUCT]
    # Get the reviews
    reviews = None
    

    # Obtenemos todas las reglas de descuento activas
    #reglas_descuento = ReglaDescuento.objects.filter(activo=True)

    # Recorrer los productos y agregar el campo 'tiene_descuento'
    for producto in products:
        # Inicializamos el campo tiene_descuento como False
        reviews = ReviewRating.objects.filter(product_id=producto.id, status=True)
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
        #print(f"descuento: {descuento}, Tiene descuento: {tiene_descuento}, porcenteje_descuento:,{porcenteje_descuento}")
        
        # Agregar el campo 'tiene_descuento' al producto
        producto.tiene_descuento = tiene_descuento
        producto.descuento = descuento
        producto.porcenteje_descuento = porcenteje_descuento


    context = {
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'home.html', context)


