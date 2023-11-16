from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from category.models import Category,SubCategory
from carts.models import CartItem
from django.db.models import Q

from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct


from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse



def store(request, category_slug=None,subcategory_slug=None):
    categories = None
    products = None
    product_count=0
    category_id = 0
    subcategy_id = 0
    subcategies = []
    categories = []
    category_name=""
    
    
    #global resolucion

    #resolucion = get_resolucion()
    #if resolucion=="":
    resolucion=settings.STORE_TEMPLATE

    user_agent = request.META.get('HTTP_USER_AGENT', '')

    if 'Mobile' in user_agent:
        print('Estás accediendo desde un celular.')
        resolucion="1"

    print("*****store***",resolucion)          
    if category_slug != None:
        if subcategory_slug != None:
            print("store 1",category_slug,subcategory_slug) 
            categories = get_object_or_404(Category.objects.order_by("category_name"), slug=category_slug)
            subcategies = get_object_or_404(SubCategory, sub_category_slug=subcategory_slug)
            products = Product.objects.filter(category=categories,subcategory=subcategies, is_available=True).order_by('product_name')
            #products = Product.objects.filter(is_available=True).order_by('product_name')
            product_count = products.count()

            paginator = Paginator(products, settings.PRODUCT_PAGE_STORE)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
        
            category_id = categories.id
            subcategy_id = subcategies.id

          

        else:
            print("store 2")
            categories = get_object_or_404(Category.objects.order_by("category_name"), slug=category_slug)
            products = Product.objects.filter(category=categories, is_available=True).order_by('product_name')
           
           
            paginator = Paginator(products, settings.PRODUCT_PAGE_STORE)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()
            category_id = categories.id
            subcategy_id = 0
    else:
        print("store 3")
 
        products = Product.objects.filter(is_available=True).order_by('product_name')
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

    if subcategies:
        sub_category_name = subcategies.subcategory_name
    else:
        sub_category_name = ""


    context = {
        'products': paged_products,
        'product_count': product_count,
        'category_id':category_id,
        'subcategory_id':subcategy_id,
        'category_name':category_name,
        'category_slug':category_slug,
        'sub_category_name':sub_category_name,
        'resolucion':resolucion
    }

    
    if resolucion == "1": #Celular
        return render(request, 'store/store.html', context)
    elif resolucion =="2":   #PC Normal
        return render(request,'store/full_store.html', context)
    elif resolucion =="3":  #Test Nuew Store
        return render(request,'store/new_store.html', context)
    else:   #Default para mariano 
        return render(request, 'store/store.html', context)
    
def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart'       : in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):

    resolucion=settings.STORE_TEMPLATE
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    if 'Mobile' in user_agent:
        print('Estás accediendo desde un celular.')
        resolucion="1"
    

    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    
    context = {
        'products': products,
        'product_count': product_count,
         'category_id':0,
        'subcategory_id':0,
        'resolucion':resolucion
    }

    if resolucion == "1": #Celular
        return render(request, 'store/store.html', context)
    elif resolucion =="2 ":   #PC Normal
        return render(request,'store/full_store.html', context)
    elif resolucion =="3":  #Test Nuew Store
        return render(request,'store/new_store.html', context)
    else:   #Default para mariano
        print("Salio por default - STORE - ")
        return render(request, 'store/store.html', context)

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
