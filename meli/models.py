from django.db import models


# Create your models here.

class meli_params(models.Model):

    client_id = models.CharField(max_length=100,unique=True)  #Cliente ID Meli
    code = models.CharField(max_length=100, blank=True)       #Codigo de autorizacion del Oauth
    access_token= models.CharField(max_length=100, blank=True) #Token de acceso a la API    "access_token": "APP_USR-5374552499309003-041109-cd983bb4d42e0db70ef149abf3699c63-4388206",
    token_type= models.CharField(max_length=100, blank=True) #"token_type": "Bearer",
    userid= models.CharField(max_length=100, blank=True)      #Usuario  que realizo la autenticacion
    refresh_token = models.CharField(max_length=100, blank=True) #Token para renovar el acceso a los recursos
    last_update = models.DateTimeField(auto_now_add=True) #Fecha y hora en que se actualizo por ultima vez
                                                          #el registro|

    def __str__(self):
        return self.code 

    class Meta:
        verbose_name = 'Meli_Param'
        verbose_name_plural = 'Meli_Params'
        ordering = ['client_id',]     
