from django.db import models
from accounts.models import Account
from store.models import Product, Variation



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

    dir_telefono = models.CharField(max_length=25)
    dir_calle = models.CharField(max_length=100)
    dir_nro = models.CharField(max_length=25)
    dir_localidad = models.CharField(max_length=50)
    dir_provincia = models.CharField(max_length=50)
    dir_cp = models.CharField(max_length=10)
    dir_obs = models.CharField(max_length=255,blank=True)
    dir_correo = models.BooleanField(default=False) #Es correo externo

    order_note = models.CharField(max_length=250, blank=True)
    order_total = models.FloatField()
    envio = models.FloatField()  #Monto Envio
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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

    def __str__(self):
        return self.product.product_name

class OrderShipping(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    user  = models.ForeignKey(Account, on_delete=models.CASCADE)
    