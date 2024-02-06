from django.shortcuts import render
from store.models import Product, ReviewRating
from django.contrib import messages

from django.conf import settings

def home(request):
    #products = Product.objects.all().filter(is_available=True).order_by('product_name')[:20]
    products = Product.objects.filter(is_available=True,is_popular=True).order_by('product_name')[:settings.POPULAR_PRODUCT]
    # Get the reviews
    reviews = None
    for product in products:
        reviews = ReviewRating.objects.filter(product_id=product.id, status=True)

    context = {
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'home.html', context)


