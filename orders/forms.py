from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'dir_telefono', 'email', 'dir_calle', 'dir_nro', 'dir_localidad', 'dir_provincia', 'dir_cp','dir_obs','dir_correo', 'order_note']
