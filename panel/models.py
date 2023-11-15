from django.db import models
from django.db.models import Sum


# Create your models here.
class ImportTempProduct(models.Model):
    product_name    = models.CharField(max_length=200) #Columna 0
    slug            = models.SlugField(max_length=200) 
    description     = models.TextField(max_length=650, blank=True) #Columna 1
    variation_category = models.CharField(max_length=25,blank=True) #Columna 2
    variation_value = models.CharField(max_length=25,blank=True) #Columna 3
    price           = models.IntegerField() #Columna 4
    images          = models.CharField(max_length=200,blank=True) #Columna 5
    stock           = models.IntegerField(default=0) #Columna 6
    is_available    = models.BooleanField(default=False) #Columna 7
    category        = models.CharField(max_length=200,blank=True) #Columna 8
    subcategory     = models.CharField(max_length=200,blank=True) #Columna 8
    created_date    = models.DateTimeField(auto_now_add=True) 
    modified_date   = models.DateTimeField(auto_now=True) 
    usuario         = models.CharField(max_length=25) 

    def __str__(self):
        return self.product_name
    
    def __unicode__(self):
        return self.product_name
    
    class Meta:
        unique_together = ('slug', 'usuario',)
        verbose_name = "ImportTempProduct"
        verbose_name_plural = "ImportTempProduct"
        ordering = ['-product_name',]

class ImportTempOrders(models.Model):
    codigo  			= models.CharField(max_length=20,unique=True) #Codigo
    first_name          =models.CharField(max_length=50,blank=True)
    last_name           =models.CharField(max_length=50,blank=True)
    email               =models.EmailField(max_length=50)
    created_at          = models.DateTimeField() #auto_now=True
    updated_at          = models.DateTimeField() #auto_now=True
    order_total         = models.FloatField()

    dir_telefono        = models.CharField(max_length=25,blank=True)
    dir_calle           = models.CharField(max_length=100,blank=True)
    dir_nro             = models.CharField(max_length=25,blank=True)
    dir_localidad       = models.CharField(max_length=50,blank=True)
    dir_provincia       = models.CharField(max_length=50,blank=True)
    dir_cp              = models.CharField(max_length=10,blank=True)
    dir_obs             = models.CharField(max_length=255,blank=True)
    dir_correo          = models.BooleanField(default=False) #Es correo externo
    usuario             = models.CharField(max_length=25) 
    status              =models.BooleanField(default=False)

    def __str__(self):
        return self.codigo


    class Meta:
        verbose_name = "ImportTempOrder"
        verbose_name_plural = "ImportTempOrders"
        ordering = ['-created_at',]
        
class ImportTempOrdersDetail(models.Model):

    codigo 	   = models.CharField(max_length=20) #Codigo
    product    = models.CharField(max_length=200)
    quantity   = models.IntegerField()
    subtotal   = models.FloatField()
    usuario    = models.CharField(max_length=25) 
    status     =models.BooleanField(default=False)

    def __str__(self):
        return self.codigo
      
      
    class Meta:
        verbose_name = "ImportTempOrdersDetail"
        verbose_name_plural = "ImportTempOrdersDetails"