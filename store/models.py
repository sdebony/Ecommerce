from django.db import models
from category.models import Category,SubCategory
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count


# Create your models here.

class Product(models.Model):

    product_name    = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True)
    description     = models.TextField(max_length=650, blank=True)
    price           = models.FloatField()
    images          = models.ImageField(upload_to='photos/products')
    imgfile         = models.TextField(max_length=300, blank=True)
    stock           = models.IntegerField()
    is_available    = models.BooleanField(default=True)
    category        = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory     = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    created_date    = models.DateTimeField(auto_now_add=True)
    modified_date   = models.DateTimeField(auto_now=True)
    is_popular      = models.BooleanField(default=False)
    peso            = models.FloatField(default=0)
    costo_prod      = models.FloatField(default=0,blank=True)
    ubicacion       = models.CharField(max_length=10,blank=True)
    precio_TN       = models.FloatField(default=0,blank=True)
    precio_ML       = models.FloatField(default=0,blank=True)
    sku_meli        = models.CharField(max_length=20,blank=True)  #MLA-1915430118
    url_meli        = models.CharField(max_length=650,blank=True) #https://articulo.mercadolibre.com.ar/MLA-1915430118-tubo-de-tenis-x-3-pelotas-tenis-head-tour-_JM

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

    def desc_item_small(self):  #Para mobile 2 lines = 60 para web 2 lineas = 70
        # Versión PC caracteres por linea:     35  --> 70 caracteres
        # Versión Mobile caracteres por linea: 22  --> 44 caracteres
        #return  self.product_name[iniciar:tamano].lower().rstrip()  +" \xa0" * (70 - tamano)

        descripcion =self.product_name.rstrip()
        tamano = len(descripcion)
        largo = 47
        #print("INICIO:",descripcion,tamano)
        iniciar = 0
        if tamano > largo: #Máximo 2 lineas mobile
            iniciar = tamano -largo +3  #Tomo los ultimos 70 caracteres
            descripcion =  "..." + descripcion[iniciar:tamano]
            tamano = len(descripcion)
            #print("Recorto -->",descripcion,iniciar,tamano)
        else:
            descripcion = descripcion + " " + "\xa0" * (largo - tamano)
            tamano = len(descripcion)
            #print("Espacios-->",descripcion,iniciar,tamano)
        
        return descripcion

    def desc_item_large(self):  #Para mobile 2 lines = 60 para web 2 lineas = 70
        # Versión PC caracteres por linea:     35  --> 70 caracteres
        # Versión Mobile caracteres por linea: 22  --> 44 caracteres
        #return  self.product_name[iniciar:tamano].lower().rstrip()  +" \xa0" * (70 - tamano)

        descripcion =self.product_name.rstrip()
        tamano = len(descripcion)
        largo = 68
        #print("INICIO:",descripcion,tamano)
        iniciar = 0
        if tamano > largo: #Máximo 2 lineas mobile
            iniciar = tamano -largo +3  #Tomo los ultimos 70 caracteres
            descripcion =  "..." + descripcion[iniciar:tamano]
            tamano = len(descripcion)
            #print("Recorto -->",descripcion,iniciar,tamano)
        else:
            descripcion = descripcion + " " + "\xa0" * (largo - tamano)
            tamano = len(descripcion)
            #print("Espacios-->",descripcion,iniciar,tamano)
        
        return descripcion

class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)

    def letras(self):
        return super(VariationManager, self).filter(variation_category='letra', is_active=True)

variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
    ('letra', 'letra'),

)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value     = models.CharField(max_length=100)
    is_active           = models.BooleanField(default=True)
    created_date        = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value

class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'

class Costo(models.Model):

    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    costo = models.FloatField()
    fecha_actualizacion = models.DateTimeField()
    usuario = models.ForeignKey(Account, on_delete=models.CASCADE)

    def __str__(self):
        return self.producto

