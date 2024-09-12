from django.db import models
from contabilidad.models import Cuentas
from store.models import Product

# Create your models here.


class CompraDolar(models.Model):

    fecha  = models.DateTimeField() 
    cuenta = models.ForeignKey(Cuentas, on_delete=models.CASCADE)
    monto=models.FloatField(default=0)
    estado=models.BooleanField(default=False)
   
    def __str__(self):
        return self.cuenta
      
      
    class Meta:
        verbose_name = "CompraDolar"
        verbose_name_plural = "CompraDolares"

class Proveedores(models.Model):

    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100,blank=True)
    direccion = models.CharField(max_length=100,blank=True)
    telefono1 = models.CharField(max_length=100,blank=True)
    telefono2 = models.CharField(max_length=100,blank=True)
    email = models.EmailField()
    web = models.CharField(max_length=100,blank=True)
    facebook = models.CharField(max_length=100,blank=True)
    instragram = models.CharField(max_length=100,blank=True)


    def __str__(self):
        return self.codigo

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

class UnidadMedida(models.Model):
    
    codigo = models.CharField(max_length=2,unique=True)  #CS  #UN
    nombre = models.CharField(max_length=50)            #Cajas #Unidades
    
    def __str__(self):
        return self.codigo
    
    class Meta:
        verbose_name = "UnidadMedida"
        verbose_name_plural = "UnidadMedida"

class Marcas(models.Model):
    
    marca = models.CharField(max_length=100,unique=True)
    descripcion = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return self.marca
    
    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

class ProveedorArticulos(models.Model):

    proveedor = models.ForeignKey(Proveedores, on_delete=models.CASCADE)
    codigo_prod_prov = models.CharField(max_length=25)
    nombre_articulo = models.CharField(max_length=100)
    marca = models.ForeignKey(Marcas, on_delete=models.CASCADE)
    descripcion = models.TextField(null=True, blank=True)
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE)
    cantidad_unidad_medida = models.FloatField(default=1)   # 24 por caja
    precio_compra = models.FloatField(default=0)
    precio_por_unidad = models.FloatField(default=0)
    peso_por_unidad = models.FloatField(default=0)
    estado = models.BooleanField(default=False)
    imagen = models.ImageField(upload_to='proveedores', null=True, blank=True)
    link = models.CharField(max_length=250,blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now_add=True)
    id_product = models.ForeignKey(Product,on_delete=models.SET_NULL,null=True)
    

    def __str__(self):
        return self.nombre_articulo

    class Meta:
        unique_together = ('proveedor', 'codigo_prod_prov','unidad_medida')
        verbose_name = "ProveedorArticulos"
        verbose_name_plural = "ProveedorArticulos"
        
