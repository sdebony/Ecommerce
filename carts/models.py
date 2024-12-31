from django.db import models
from store.models import Product, Variation, ReglaDescuento
from accounts.models import Account


# Create your models here.

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

#Los valores de los descuentos son totales en esta linea
class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart    = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    precio_real = models.FloatField(default=0, blank=True, null=True)
    desc_unit = models.FloatField(default=0, blank=True, null=True)
    precio_con_desc= models.FloatField(default=0, blank=True, null=True)
    sub_total_linea = models.FloatField(default=0, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        #return self.product.price * self.quantity
        return self.sub_total_linea
    
    def porcentaje_desc(self):
        # Obtiene todos los porcentajes de descuento y sus nombres asociados al CartItem
        descuentos = CartItemDescuento.objects.filter(cartitemid=self)
        return [{'porcentaje': descuento.porcentaje_descuento, 'nombre': descuento.regladescuento.nombre} for descuento in descuentos]



    def __unicode__(self):
        return self.product

class CartItemDescuento(models.Model):

    cartitemid = models.ForeignKey(CartItem, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    descuento_unit = models.FloatField()
    descuento_total = models.FloatField()
    porcentaje_descuento = models.IntegerField()
    regladescuento = models.ForeignKey(ReglaDescuento, on_delete=models.CASCADE, null=True)


    def __str__(self):
        return self.cartitemid

class CartItemKit(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart    = models.ForeignKey(CartItem, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
   
    def __unicode__(self):
        return self.product
    
  