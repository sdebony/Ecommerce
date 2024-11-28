from rest_framework import serializers


from accounts.models import AccountDirecciones
from contabilidad.models import Cuentas
from category.models import SubCategory, Category
from store.models import Product


class DireccionesSerializer(serializers.ModelSerializer):

    class Meta:
        model=AccountDirecciones
        fields='__all__'

class CuentasSerializer(serializers.ModelSerializer):
    class Meta:
        model=Cuentas
        fields='__all__'
        
class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=SubCategory
        fields='__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields='__all__'

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields='__all__'