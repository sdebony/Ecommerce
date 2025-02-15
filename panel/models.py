from django.db import models
from django.db.models import Sum
from accounts.models import Account


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
    peso            = models.FloatField(default=0)
    ubicacion       = models.CharField(max_length=10,blank=True)
    costo_prod      = models.FloatField(default=0,blank=True)

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
    dir_tipocorreo      = models.BigIntegerField(default=0) #1 (Sucursal) #2(Envio a Domiciloi) #3(Retira Cliente)
    usuario             = models.CharField(max_length=25) 
    status              =models.BooleanField(default=False)

    def __str__(self):
        return self.codigo


    class Meta:
        verbose_name = "ImportTempOrder"
        verbose_name_plural = "ImportTempOrders"
        ordering = ['-created_at',]
        
class ImportTempOrdersDetail(models.Model):

    codigo 	   = models.ForeignKey(ImportTempOrders, on_delete=models.CASCADE)  
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

class ImportDolar(models.Model):

    created_at  = models.DateTimeField()
    codigo      = models.CharField(max_length=50) #blue 
    moneda      = models.CharField(max_length=5)  #USD
    nombre      = models.CharField(max_length=50) #Blue
    compra      = models.FloatField()
    venta       = models.FloatField()
    promedio    = models.FloatField()
    fechaActualizacion =models.DateTimeField() #auto_now=True
   
    def __str__(self):
        return self.codigo
      
      
    class Meta:
        verbose_name = "ImportDolar"
        verbose_name_plural = "ImportDolar"

class Alerta(models.Model):
    usuario = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='alertas')
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True,null=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titulo