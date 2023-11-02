from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


from .serializers import DireccionesSerializer,CuentasSerializer, SubcategorySerializer
from accounts.models import AccountDirecciones,Account
from contabilidad.models import Cuentas
from category.models import SubCategory

from django.db.models import Q

from django.conf import settings


class Direccion(APIView):
          
    def get(self,request,dir_id):
        print("Direccion API ",dir_id)
        if dir_id==99:
            user_id = Account.objects.filter(email=settings.EMAIL_HOST_USER).first()
            print("Retira por capital. direccion 99 lifche usuario ",user_id)
            if user_id:
                direccion = get_object_or_404(AccountDirecciones,dir_id=dir_id,user=user_id)
        else:
            direccion = get_object_or_404(AccountDirecciones,dir_id=dir_id)
        data = DireccionesSerializer(direccion).data
        print(data)
        return Response(data)


class DireccionesList(APIView):
          
    def get(self,request):
        print("Lista de Direcciones")
        direccion = get_object_or_404(AccountDirecciones)
        data = DireccionesSerializer(direccion,many=True).data
        return Response(data)

class CuentasList(APIView):
          
    def get(self,request,cuenta):
        print("Cuentas API List")
        cuentas = get_object_or_404(Cuentas,Q(id=cuenta))
        data = CuentasSerializer(cuentas).data
        return Response(data)

class CuentasApi(APIView):
          
    def get(self,request):
        print("Cuentas API ")
        cuentas = Cuentas.objects.all()
        data = CuentasSerializer(cuentas,many=True).data
        return Response(data)

class SubcategoryList(APIView):
          
    def get(self,request,category):
        print("SubCategory API List")
        #subcategory = get_object_or_404(SubCategory,Q(category=category))
        subcategory = SubCategory.objects.filter(Q(category=category))
        data = SubcategorySerializer(subcategory,many=True).data
        return Response(data)

class SubcategoryApi(APIView):
          
    def get(self,request):
        print("SubCategory API ")
        subcategory = SubCategory.objects.all()
        data = SubcategorySerializer(subcategory,many=True).data
        return Response(data)


     
     