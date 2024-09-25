from django.db import models
from contabilidad.models import Cuentas,Movimientos
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
        return self.nombre

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
        unique_together = ('proveedor', 'codigo_prod_prov','unidad_medida','nombre_articulo')
        verbose_name = "ProveedorArticulos"
        verbose_name_plural = "ProveedorArticulos"
        ordering = ['nombre_articulo']

        
class ComprasEnc(models.Model):

    fecha_compra=models.DateField(null=True,blank=True)
    observacion=models.TextField(blank=True,null=True)
    sub_total=models.FloatField(default=0)
    costoenvio=models.FloatField(default=0)
    descuento=models.FloatField(default=0)
    total=models.FloatField(default=0)
    proveedor=models.ForeignKey(Proveedores,on_delete=models.CASCADE)
    estado=models.IntegerField(default=0)
    id_pago = models.IntegerField(default=0,blank=True,null=True)
    
    def __str__(self):
        return '{}'.format(self.observacion)

    def save(self, *args, **kwargs):
        # Convierte la observación a mayúsculas
        self.observacion = self.observacion.upper()

        # Asignar valores por defecto si son None
        if self.sub_total is None:
            self.sub_total = 0
        if self.descuento is None:
            self.descuento = 0

        # Calcular el total
        self.total = self.sub_total - self.descuento + self.costoenvio

        # Llamar al método original save() con los argumentos y parámetros adicionales
        super(ComprasEnc, self).save(*args, **kwargs)


    class Meta:
        verbose_name_plural = "Encabezado Compras"
        verbose_name="Encabezado Compra"

class ComprasDet(models.Model):
    id_compra_enc = models.ForeignKey(ComprasEnc, on_delete=models.CASCADE)
    producto=models.ForeignKey(ProveedorArticulos,on_delete=models.CASCADE)
    cantidad=models.BigIntegerField(default=0)
    precio_prv=models.FloatField(default=0)
    sub_total=models.FloatField(default=0)
    descuento=models.FloatField(default=0)
    total=models.FloatField(default=0)
    

    def __str__(self):
        return '{}'.format(self.producto)


     # Ajustar el método save para aceptar los parámetros adicionales
    def save(self, *args, **kwargs):
        self.sub_total = float(self.cantidad) * float(self.precio_prv)
        self.total = self.sub_total - float(self.descuento)
        # Llamar al método save original con los parámetros adicionales
        super(ComprasDet, self).save(*args, **kwargs)

    
    class Mega:
        verbose_name_plural = "Detalle Compras"
        verbose_name="Detalle Compra"

