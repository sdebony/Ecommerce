from django.db import models

from django.db.models import Sum

from orders.models import Order
# Create your models here.


class Monedas(models.Model):

    codigo = models.CharField('Codigo', max_length=25)
    simbolo = models.CharField('Simbolo',max_length=5)
    descripcion = models.CharField('Descripcion',max_length=100)

    def __str__(self):
        return '{}'.format(self.codigo) 

    def moneda(self):
        return f'{self.simbolo} {self.codigo}'

    class Meta:        
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"

class Cuentas(models.Model):

    nombre      = models.CharField('Nombre', max_length=25,unique=True)
    descripcion = models.CharField('Descripcion',max_length=50,default='')
    moneda      =  models.ForeignKey(Monedas, on_delete=models.CASCADE, null=False)
    limite      = models.IntegerField(default=0) #Importe maximo mensual
    is_available    = models.BooleanField(default=True)
    
    def __str__(self):
        return '{}'.format(self.nombre) #+ ' - ' +'{}'.format(self.moneda) + ' - ' +'{}'.format(self.id)

    def codigo(self):
        return f'{self.moneda.codigo}'

  
    class Meta:        
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"
        
class Operaciones(models.Model):
        
    codigo = models.CharField(max_length=3)
    movimiento=models.CharField(max_length=25)

    def __str__(self):
        return '{}'.format(self.codigo)

    class Meta:
        verbose_name = "Operacion"
        verbose_name_plural = "Operaciones"
        
class Movimientos(models.Model):

    fecha = models.DateField() 
    cliente = models.CharField(max_length=100,null=True,default='')
    movimiento=models.ForeignKey(Operaciones, on_delete=models.CASCADE,null=False)
    cuenta = models.ForeignKey(Cuentas, on_delete=models.CASCADE)
    monto=models.FloatField(default=0)
    observaciones = models.CharField(max_length=250,default='',null=False,blank=True)
    idtransferencia = models.BigIntegerField(default=0)
    ordernumber = models.ForeignKey(Order,on_delete=models.CASCADE,null=True)


    def __str__(self):
        return '{}'.format(self.id)


    class Meta:
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha','-id',]

class Transferencias(models.Model):

    fecha = models.DateField() 
    cliente = models.CharField(max_length=100,null=True,default='')
    movimiento=models.ForeignKey(Operaciones, on_delete=models.CASCADE,null=False)
    cuenta_origen = models.ForeignKey(Cuentas, on_delete=models.CASCADE,related_name='cuenta_origen')
    cuenta_destino = models.ForeignKey(Cuentas, on_delete=models.CASCADE,related_name='cuenta_destino')
    monto_origen=models.FloatField(default=0)
    conversion=models.FloatField(default=0)
    monto_destino=models.FloatField(default=0)
    observaciones = models.CharField(max_length=250,default='',null=False,blank=True)
    idmov_origen = models.ForeignKey(Movimientos,on_delete=models.CASCADE,null=True,related_name='mov_origen')
    idmov_destino = models.ForeignKey(Movimientos,on_delete=models.CASCADE,null=True,related_name='mov_destino')


    def __str__(self):
        return '{}'.format(self.id)


    class Meta:
        verbose_name_plural = "Transferencias"
        ordering = ['-fecha','-id',]