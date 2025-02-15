from django.db import models


import calendar

import locale

# Configurar la localización a español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

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
    documento    = models.CharField('Documento', max_length=25,default='')
    nro_cuenta    = models.CharField('Nro Cuenta', max_length=25,default='')
    cbu    = models.CharField('CBU', max_length=25,default='')
    cuil    = models.CharField('Cuil', max_length=25,default='')
    alias    = models.CharField('Alias', max_length=50,default='')
    
    def __str__(self):
        return '{}'.format(self.nombre) #+ ' - ' +'{}'.format(self.moneda) + ' - ' +'{}'.format(self.id)

    def codigo(self):
        return f'{self.moneda.codigo}'

  
    class Meta:        
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"

class CierreMes(models.Model):

    fecha = models.DateField()
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField()
    mes = models.BigIntegerField(default=0)
    anio = models.BigIntegerField(default=0)
    ing_saldo_pesos = models.FloatField(default=0)
    ing_saldo_dolar = models.FloatField(default=0)
    egr_saldo_pesos = models.FloatField(default=0)
    egr_saldo_dolar = models.FloatField(default=0)
    tot_saldo_pesos = models.FloatField(default=0)
    tot_saldo_dolar = models.FloatField(default=0)

    def __str__(self):
        return '{}'.format(self.id)

    def get_mes_display(self):
        return calendar.month_name[self.mes]

    class Meta:
        unique_together = ('mes', 'anio')  # Define la combinación única de mes y año
        verbose_name_plural = "Cierre Mesual"
        ordering = ['-anio','-mes',]

class Cierres(models.Model): #NO SE USA

    fecha = models.DateField(null=False) 
    mes = models.BigIntegerField(null=False)
    ano = models.BigIntegerField(null=False)
    cuenta = models.ForeignKey(Cuentas, on_delete=models.CASCADE)
    total_ultimo_cierre=models.FloatField(default=0) #Saldo cierre anterior ajustado (REAL)
    total_movimientos_registrados=models.FloatField(default=0) #Sumatoria de movimientos (ING + EGR) en el período
    total_saldo_real=models.FloatField(default=0)  # Saldo real de la cuenta
    total_diferencia=models.FloatField(default=0)  # Saldo real - total movimientos registrados
    observaciones = models.CharField(max_length=250,default='',null=False,blank=True)

    def __str__(self):
        return '{}'.format(self.id)


    class Meta:
        verbose_name_plural = "Cierres"
        ordering = ['-fecha','-id',]

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
    idcierre = models.BigIntegerField(default=0)
    

    def __str__(self):
        return '{}'.format(self.id)


    class Meta:
        verbose_name = "Movimiento"
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
        verbose_name_plural = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering = ['-fecha','-id',]

class ConfiguracionParametros(models.Model):
    
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=10,null=False,blank=False)  #MG1: Margen 1 MG2: Margen 2 MG3: Margen 3 COM1: Comision 1 COM2: Comision 2
    nombre = models.CharField(max_length=100, null=False, blank=False) #Margen 1
    valor = models.FloatField(default=0)  # 10
    tipo_valor = models.CharField(max_length=1,null=False,blank=False) # % o $
    descripcion = models.CharField(max_length=100, null=False, blank=False) #Margen 1 surge del costo * margen1 
    
    def __str__(self):
        return '{}'.format(self.id)

    class Meta:
        verbose_name_plural = "Parametros"
        verbose_name_plural = "Configuracion Parametros"
        ordering = ['id',]
        
        