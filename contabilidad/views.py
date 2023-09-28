
from django.shortcuts import render, get_object_or_404,redirect
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import AccountPermition

from .models import Cuentas,Monedas

# Create your views here.

def cuentas_list(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CUENTAS')
            if accesousuario:
                if accesousuario.modo_ver==False:
                   print("Sin acceso a ver pedidos")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CUENTAS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
        cuentas = Cuentas.objects.filter()
        cantidad = cuentas.count()

      
        context = {
            'cuentas':cuentas,
            'cantidad':cantidad,
            'permisousuario':permisousuario,
           
        }
       
        return render(request,'contabilidad/lista_cuentas.html',context) 

    return render(request,'panel/login.html',)

def cuentas_detalle(request,cta_id=None):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CUENTAS')
            if accesousuario:
                if accesousuario.modo_editar==False:
                   print("Sin acceso a modificar cuentas")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL
   
    if accesousuario.codigo.codigo =='CUENTAS':

        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
         
        if request.method =="GET":

            if cta_id:       
                cuentas = Cuentas.objects.get(id=cta_id)
            else:
                cuentas = Cuentas.objects.filter()

            monedas = Monedas.objects.filter()
            
        
            context = {
                'cuentas':cuentas,
                'monedas':monedas,
                'permisousuario':permisousuario,
            
            }
        
            return render(request,'contabilidad/cuentas_form.html',context) 

        if request.method =="POST":
            
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion")
            moneda = request.POST.get("moneda")
            habilitado = request.POST.getlist("is_available")
            limite = request.POST.get("limite")

            
            if habilitado:
                is_available=True
            else:
                is_available = False

            print(is_available,"is_available")
            print(nombre,"nombre")


            if cta_id:
                cuentas = Cuentas.objects.get(id=cta_id)
                monedas = Monedas.objects.filter(codigo=moneda).first()

                if cuentas:
                    #UPDATE
                    print("POST --> UPDATE")
                    # UPDATE 
                    cuentas = Cuentas(
                        id=cta_id ,
                        nombre=nombre,
                        descripcion=descripcion,
                        moneda=monedas,
                        limite=limite,
                        is_available=is_available,
                        
                    )
                    cuentas.save()
                else:
                    print("cuenta no encontrada")
            else:
                 print("POS --> ADD")
                 cuentas = Cuentas(
                        nombre=nombre,
                        descripcion=descripcion,
                        moneda=moneda,
                        limite=limite,
                        is_available=habilitado,
                 )
                 cuentas.save()
                 cta_id=cuentas.id
            
            cuentas = Cuentas.objects.get(id=cta_id)
            context = {
                'cuentas':cuentas,
                'monedas':monedas,
                'permisousuario':permisousuario,
            
                }
            return redirect('conta_list_cuentas')                
           
    return render(request,'panel/login.html',)

def cuentas_new(request):
    
    try:
        if request.user.is_authenticated:
            accesousuario =  get_object_or_404(AccountPermition, user=request.user, codigo__codigo ='CUENTAS')
            if accesousuario:
                if accesousuario.modo_editar==False:
                   print("Sin acceso a crear cuentas")
                   return render(request,'panel/login.html',)  
        else:
            return render(request,'panel/login.html',)  
    except ObjectDoesNotExist:
            return render(request,'panel/login.html',)

    #Si tiene acceso a PANEL 
    if accesousuario.codigo.codigo =='CUENTAS':
        permisousuario = AccountPermition.objects.filter(user=request.user).order_by('codigo__orden')
         
        if request.method =="GET":

   
            cuentas = []
            monedas = Monedas.objects.filter()
        
            context = {
                'cuentas':cuentas,
                'monedas':monedas,
                'permisousuario':permisousuario,
            
            }
        
            return render(request,'contabilidad/cuentas_form.html',context) 

        if request.method =="POST":
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion")
            moneda = request.POST.get("moneda")
            habilitado = request.POST.getlist("is_available")
            limite = request.POST.get("limite")

            if not limite:
                limite = 0
            if habilitado:
                is_available=True
            else:
                is_available = False

      
            monedas = Monedas.objects.filter(codigo=moneda).first()
            cuentas = Cuentas(
                    nombre=nombre,
                    descripcion=descripcion,
                    moneda=monedas,
                    limite=limite,
                    is_available=is_available,
                 )
            cuentas.save()
            
            context = {
                'cuentas':cuentas,
                'monedas':monedas,
                'permisousuario':permisousuario,
            
                }
            return redirect('conta_list_cuentas')                
           

    return render(request,'panel/login.html',)