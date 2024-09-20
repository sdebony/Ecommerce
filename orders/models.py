from django.db import models
from accounts.models import Account

from store.models import Product, Variation, Costo



class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100) # this is the total amount paid
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id


class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled','Cancelled'),
        ('Cobrado', 'Cobrado'),
        ('Entregado', 'Entregado'),

    )
    
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    fecha = models.DateField(blank=True)

    dir_nombre = models.CharField(max_length=25,blank=True)
    dir_telefono = models.CharField(max_length=25)
    dir_calle = models.CharField(max_length=100,blank=True)
    dir_nro = models.CharField(max_length=25,blank=True)
    dir_localidad = models.CharField(max_length=50,blank=True)
    dir_provincia = models.CharField(max_length=50,blank=True)
    dir_cp = models.CharField(max_length=10,blank=True)
    dir_obs = models.CharField(max_length=255,blank=True)
    dir_tipocorreo = models.BigIntegerField(default=0) #1 Sucursal Correo  #2 Envio a Domicilio #3 Retiro en Tienda
    dir_tipoenvio = models.BigIntegerField(default=0,blank=True)  #1-Clasico  #2-Expresso

    order_note = models.CharField(max_length=250, blank=True)
    order_total = models.FloatField()
    envio = models.FloatField()  #Monto Envio
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_peso = models.FloatField(default=0)
    cuenta    = models.BigIntegerField(default=0)

    fecha_tracking = models.DateTimeField(blank=True,null=True)
    nro_tracking = models.CharField(max_length=50, blank=True)
    

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def full_address(self):
        return f'{self.dir_calle} {self.dir_nro}'

    def __str__(self):
        return self.first_name

    def status_id(self):
        return f'{self.status}'

    @classmethod
    def get_totales(cls):
        return sum([Order.order_total for Orders in cls.objects.all()])
            

    class Meta:
        
        verbose_name = "Order"
        verbose_name_plural = "Ordenes"
        ordering = ['-order_number',]

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    costo = models.FloatField(default=0)


    def __str__(self):
        return self.product.product_name
    
    def subtotal(self):
        return self.quantity*self.product_price


class OrderShipping(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    user  = models.ForeignKey(Account, on_delete=models.CASCADE)
    
    