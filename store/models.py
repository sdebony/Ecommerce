from django.db import models
from category.models import Category,SubCategory
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count
from django.utils import timezone


# Create your models here.

class Product(models.Model):

    product_name    = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True)
    description     = models.TextField(max_length=650, blank=True)
    price           = models.FloatField()
    images          = models.ImageField(upload_to='photos/products')
    imgfile         = models.TextField(max_length=300, blank=True)
    stock           = models.IntegerField()
    stock_minimo    = models.IntegerField(default=0,blank=True)
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
    sku_meli        = models.CharField(max_length=420,blank=True)  #MLA-1915430118
    url_meli        = models.CharField(max_length=650,blank=True) #https://articulo.mercadolibre.com.ar/MLA-1915430118-tubo-de-tenis-x-3-pelotas-tenis-head-tour-_JM
    es_kit          = models.BooleanField(default=False)


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

    class Meta:
        verbose_name = 'Costo'
        verbose_name_plural = 'Costo'

class ProductKitEnc(models.Model):
    
    productokit = models.ForeignKey(Product, on_delete=models.CASCADE)
    cant_unidades = models.FloatField()
    cant_variedades = models.FloatField()
    
    def __str__(self):
        return str(self.productokit)  # Utiliza str() para evitar errores de tipo

    class Meta:
        verbose_name = 'producto kit encabezado'
        verbose_name_plural = 'producto kit encabezado'

class ProductKit(models.Model):

    productokit = models.ForeignKey(ProductKitEnc, on_delete=models.CASCADE)
    productohijo = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    
    def __str__(self):
        return str(self.productohijo)  # Utiliza str() para evitar errores de tipo

    class Meta:
        verbose_name = 'producto_kit'
        verbose_name_plural = 'producto_kit'
        unique_together = ('productokit', 'productohijo')

class ReglaDescuento(models.Model):
    TIPOS_DESCUENTO = [
        ('porcentaje', 'Porcentaje'),  # Descuento en porcentaje
        ('fijo', 'Monto Fijo'),        # Rango Ventas Mayores a 100 y menores a 200 ... Se toma monto_desde y monto hasta
    ]

    nombre = models.CharField(max_length=200)
    tipo_descuento = models.CharField(
        max_length=20, 
        choices=TIPOS_DESCUENTO, 
        default='porcentaje'
    )
    valor_descuento = models.FloatField()
    cantidad_minima = models.IntegerField(
        default=0, 
        blank=True, 
        null=True
    )
    fecha_inicio = models.DateTimeField(
        blank=True, 
        null=True
    )
    fecha_fin = models.DateTimeField(
        blank=True, 
        null=True
    )
    activo = models.BooleanField(default=True)
    categoria = models.ManyToManyField(Category,  blank=True)    
    subcategoria = models.ManyToManyField(SubCategory,  blank=True)
    productos = models.ManyToManyField(Product, blank=True)
    monto_desde = models.FloatField()
    monto_hasta = models.FloatField()
    acumulable = models.BooleanField(default=False)
   
    # Método para verificar si el descuento es aplicable

    #def obtener_nombre_descuento(self,producto):
    #
    #    if not self.es_aplicable(producto, 0):
    #        return 0
    #
    #    if self.tipo_descuento.strip().upper() == 'PORCENTAJE':
    #        return str(self.valor_descuento) + ' %' 
    #    #elif self.tipo_descuento.strip().upper() == 'FIJO':  #El fijo es por rango de venta final no se muestra en los articulos
    #    #    return "$ -" + str(self.valor_descuento) + " OFF" 
    #
    #    return 0


    # Método para calcular el descuento
    #def calcular_descuento(self, producto, cantidad):
    #    """
    #    Calcula el descuento total aplicable basado en el tipo y valor del descuento.
    #    """
    #    if not self.es_aplicable(producto, cantidad):
    #        return 0

    #    if self.tipo_descuento == 'porcentaje':
    #        return producto.price * (self.valor_descuento / 100) * cantidad
    #    elif self.tipo_descuento == 'fijo':
    #        return self.valor_descuento * cantidad

    #    return 0

    def __str__(self):
        return self.nombre
    class Meta:
        verbose_name = "Regla de Descuento"
        verbose_name_plural = "Reglas de Descuento"
        ordering = ['nombre']
