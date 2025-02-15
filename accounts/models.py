from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# Create your models here.

class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('User must have an email address')

        if not username:
            raise ValueError('User must have an username')

        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, username, password):
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

class Account(AbstractBaseUser):
    first_name      = models.CharField(max_length=50)
    last_name       = models.CharField(max_length=50)
    username        = models.CharField(max_length=50, unique=True)
    email           = models.EmailField(max_length=100, unique=True)
    phone_number    = models.CharField(max_length=50)

    # required
    date_joined     = models.DateTimeField(auto_now_add=True)
    last_login      = models.DateTimeField(auto_now_add=True)
    is_admin        = models.BooleanField(default=False)
    is_staff        = models.BooleanField(default=False)
    is_active        = models.BooleanField(default=False)
    is_superadmin        = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True

class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    profile_picture = models.ImageField(blank=True, upload_to='userprofile')
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)


    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

class Permition(models.Model):
    codigo  = models.CharField(max_length=25)
    permiso = models.CharField(max_length=100)
    rootpath = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255,blank=True)
    orden   = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.codigo}'

class AccountPermition(models.Model):

     user = models.ForeignKey(Account, on_delete=models.CASCADE)
     codigo = models.ForeignKey(Permition,on_delete=models.CASCADE)
     modo_ver = models.BooleanField(default=False)
     modo_editar = models.BooleanField(default=False)

     def __str__(self):
        return f'{self.codigo}'

class AccountDirecciones(models.Model):

     dir_id = models.AutoField('dir_id',primary_key=True)
     user = models.ForeignKey(Account, on_delete=models.CASCADE)
     dir_nombre = models.CharField(max_length=50)
     dir_cp = models.CharField(max_length=10)
     dir_calle = models.CharField(max_length=100)
     dir_nro = models.CharField(max_length=25)
     dir_piso = models.CharField(max_length=10,blank=True)
     dir_depto = models.CharField(max_length=10,blank=True)
     dir_localidad = models.CharField(max_length=50,blank=True)
     dir_provincia = models.CharField(max_length=50,blank=True)
     dir_area_tel = models.CharField(max_length=5,blank=True)
     dir_telefono = models.CharField(max_length=25)
     dir_obs    = models.CharField(max_length=250,blank=True)
     dir_tipocorreo = models.BigIntegerField(default=0) #1 Envio a Domicilio  #2 Sucursal Correo  
     dir_tipoenvio = models.BigIntegerField(default=0)  #1-Clasico  #2-Expreso
     dir_correo = models.BigIntegerField(default=0) # 1-OCA  #2 Correo Argentino #3 Retira Cliente

     def __str__(self):
        return f'{self.dir_id}'

class BillingInfo(models.Model):
    
    order = models.CharField(max_length=20,unique=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    identification_type = models.CharField(max_length=50)
    identification_number = models.CharField(max_length=50)
    taxpayer_type_id = models.CharField(max_length=10)
    taxpayer_type_description = models.CharField(max_length=100)
    street_name = models.CharField(max_length=200)
    street_number = models.CharField(max_length=50)
    city_name = models.CharField(max_length=100)
    state_code = models.CharField(max_length=10)
    state_name = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country_id = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.order}'

    class Meta:
        
        verbose_name = "BillingInfo"
        verbose_name_plural = "BillingInfo"
        
        

