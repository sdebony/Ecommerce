from django.db import models
from contabilidad.models import Cuentas

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