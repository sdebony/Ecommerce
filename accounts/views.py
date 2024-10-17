from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile,AccountPermition,Permition, AccountDirecciones
from orders.models import Order, OrderProduct
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests


def register(request):

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            phone_number=phone_number.replace(" ","")
            
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # Create a user profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            #print(email)
            messages.success(request, 'Gracias por registrarse. Le enviamos un correo de verificación.')
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # Getting the product variations by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    # product_variation = [1, 2, 3, 4, 6]
                    # ex_var_list = [4, 6, 3, 5]

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Felicitaciones! Tu cuenta ya esta activa.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')

@login_required(login_url = 'login')
def dashboard(request):

        print("Dashboard Account Inicial")
        if request.user.is_authenticated and request.user.is_staff:
            id_permiso = Permition.objects.get(codigo='PANEL')
            if id_permiso:
                accesousuario =  AccountPermition.objects.filter(user=request.user.id, codigo=id_permiso,modo_ver=True)  #Permiso de Ver  
                try:
                    if accesousuario:
                        return redirect('panel')
                        
                    else:
                        print("Sin Acceso Panel")
                        orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
                        orders_count = orders.count()

                        userprofile = UserProfile.objects.filter(user_id=request.user.id).first()
                        if not userprofile:
                            user_profile = UserProfile (
                                user = request.user,
                                address_line_1 = "",
                                address_line_2 = "",
                                profile_picture = "userprofile/default_user.png",
                                city="",
                                state = "",
                                country = ""
                            )
                            user_profile.save()
                            userprofile =  get_object_or_404(UserProfile, user_id=request.user.id)
                
                        context = {
                            'orders_count': orders_count,
                            'userprofile': userprofile,
                        }
                        print("accounts/dashboard.html")
                        return render(request, 'accounts/dashboard.html', context)  

                except ObjectDoesNotExist:
                    print("Sin Acceso Panel")
                    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
                    orders_count = orders.count()
           
                    userprofile = UserProfile.objects.get(user_id=request.user.id)
                
                    context = {
                        'orders_count': orders_count,
                        'userprofile': userprofile,
                    }
                    print("accounts/dashboard.html")
                
                    return render(request, 'accounts/dashboard.html', context)
                 
            else:
                print("Sin Acceso Panel")
                orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
                orders_count = orders.count()

                userprofile = UserProfile.objects.get(user_id=request.user.id)
        
                context = {
                    'orders_count': orders_count,
                    'userprofile': userprofile,
                }
                print("accounts/dashboard.html")
                return render(request, 'accounts/dashboard.html', context)     
        
        else:
            print("Sin Acceso Panel")
            orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
            orders_count = orders.count()
            userprofile = UserProfile.objects.filter(user_id=request.user.id).first()
            if not userprofile:
                user_profile = UserProfile (
                    user = request.user,
                    address_line_1 = "",
                    address_line_2 = "",
                    profile_picture = "userprofile/default_user.png",
                    city="",
                    state = "",
                    country = ""
                )
                user_profile.save()
                userprofile =  get_object_or_404(UserProfile, user_id=request.user.id)


            context = {
                'orders_count': orders_count,
                'userprofile': userprofile,
            }
            print("accounts/dashboard.html")
        
            return render(request, 'accounts/dashboard.html', context)

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('login')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):

    if request.user.is_admin == True:
        orders = Order.objects.filter(is_ordered=True,order_number__regex=r'^[0-9]*$').order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user, is_ordered=True,order_number__regex=r'^[0-9]*$').order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)

@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request, order_id):

    #order_detail = OrderProduct.objects.filter(order__order_number__regex=r'^[0-9]*$', order__order_number=order_id) #Filtro los numericos
    order_detail = OrderProduct.objects.filter(order__order_number=order_id) 
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)

@login_required(login_url='login')
def edit_dir_entrega(request):

  
    if request.method=='POST':

        print("Entre a edit_dir_entrega *********************")
        button_press = request.POST.get('action')   
        print("Accion:",button_press)
        
        #*****  O C A ****************
        if button_press=='save_oca_ed':
            # 1-OCA  ENTREGA A DOMICILIO
            dir_tipocorreo_1 = request.POST.get('dir_tipocorreo_1')  
            if dir_tipocorreo_1 == '1':
                #DATOS OCA ENVIO A DOMICILIO
                    print("Datos OCA Envio a Domicilio")
                    dir_id_1= request.POST["dir_id_1"]                  #ID Direccion Entrega OCA
                    dir_correo = 1                                      #OCA
                    dir_nombre_1 = request.POST["dir_nombre_1"]         # Alias Direccion Entrega
                    dir_tipoenvio_1 = 0                                 #  OCA NO TIENE TIPO ENVIO   # 1 Clasico 2-Expreso
                    dir_cp_1 = request.POST['dir_cp_1']                 #Codigo Postal
                    dir_calle_1= request.POST["dir_calle_1"]            # Calle de envio a domicilio
                    dir_nro_1= request.POST["dir_nro_1"]                #Nro Calle de envio a domicilio
                    dir_piso_1= request.POST["dir_piso_1"]              #Piso
                    dir_depto_1= request.POST["dir_depto_1"]            #Depto
                    dir_localidad_1= request.POST["dir_localidad_1"]    #Localidad
                    dir_provincia_1= request.POST["dir_provincia_1"]    #Provincia envio a domicilio
                    dir_area_tel_1= request.POST["dir_area_tel_1"]
                    dir_telefono_1= request.POST["dir_telefono_1"]
                    dir_obs_1= request.POST["dir_obs_1"]
                    dir_tipocorreo_1 = request.POST['dir_tipocorreo_1'] # Envio a Domicilio / Retira Sucursal 
                   

                    if dir_id_1 == "" or dir_id_1 == "0":
                        #ADD NEW
                        print("ADD NEW Direccion Entrega OCA")
                        direcciones = AccountDirecciones(
                                dir_nombre=dir_nombre_1,
                                user=request.user,
                                dir_correo=dir_correo,
                                dir_cp=dir_cp_1,
                                dir_calle=dir_calle_1,
                                dir_nro=dir_nro_1,
                                dir_piso=dir_piso_1,
                                dir_depto=dir_depto_1,
                                dir_localidad=dir_localidad_1,
                                dir_provincia=dir_provincia_1,
                                dir_area_tel=dir_area_tel_1,
                                dir_telefono=dir_telefono_1,
                                dir_obs=dir_obs_1,
                                dir_tipoenvio=dir_tipoenvio_1,
                                dir_tipocorreo=dir_tipocorreo_1,
                            )
                        direcciones.save()
                        print("Direccion de Entrega OCA Agregada")
                        messages.success(request,'Se ha agregado la Dirección de Entrega correctamente!')
                    else:
                        #UPDATE
                        print("UPDATE Direccion Entrega OCA")
                        
                        direcciones = AccountDirecciones.objects.get(dir_id=dir_id_1)
                        direcciones.dir_id = dir_id_1
                        direcciones.dir_nombre = dir_nombre_1
                        direcciones.dir_cp = dir_cp_1
                        direcciones.dir_calle = dir_calle_1
                        direcciones.dir_cp = dir_cp_1
                        direcciones.dir_nro = dir_nro_1
                        direcciones.dir_piso = dir_piso_1
                        direcciones.dir_depto = dir_depto_1
                        direcciones.dir_provincia = dir_provincia_1
                        direcciones.dir_localidad = dir_localidad_1
                        direcciones.dir_area_tel = dir_area_tel_1
                        direcciones.dir_telefono = dir_telefono_1
                        direcciones.dir_obs = dir_obs_1
                        direcciones.dir_tipocorreo = dir_tipocorreo_1   #Envio a Domicilio
                        direcciones.dir_correo = 1           #OCA (1)
                        direcciones.dir_tipoenvio = 0        #OCA no tiene Clasico , Express
                        direcciones.save()
                        messages.success(request,'Se ha actualizado la Dirección de Entrega correctamente!')
        if button_press=='save_oca_rs':
            #OCA RETIRO EN SUCURSAL
            dir_tipocorreo_2 = request.POST.get('dir_tipocorreo_2')
            if dir_tipocorreo_2 == '2':    
                    
                    dir_id_2 = request.POST.get('dir_id_2')  #ID DIRECC
                    dir_nombre_2 = request.POST.get('dir_nombre_2','')  #Nombre Direccion
                    dir_cp_2 =request.POST.get('dir_cp_2','')             #Código Postal D
                    dir_calle_2 = request.POST.get('dir_calle_2','')       #Calle
                    dir_nro_2 =request.POST.get('dir_nro_2','')                #Nro
                    dir_provincia_2 = request.POST.get('dir_provincia_2', '') #Provincia
                    dir_localidad_2 = request.POST.get('dir_localidad_2', '') #Localidad
                    dir_area_tel_2 =request.POST.get('dir_area_tel_2', '')  #Area Tel
                    dir_telefono_2 =request.POST.get('dir_telefono_2', '')  #Telefono
                    dir_obs_2 =request.POST.get('dir_obs_2', '')     #Observacion
                    dir_tipoenvio_2 = 0                             #OCA NO TIENE CLASICO NI EXPRESS
                    dir_correo = 1                                  # OCA  
                    
                    if not dir_id_2:
                        #ADD NEW
                        
                        direcciones = AccountDirecciones(
                                dir_nombre=dir_nombre_2,
                                user=request.user,
                                dir_cp=dir_cp_2,
                                dir_correo = dir_correo,
                                dir_calle=dir_calle_2,
                                dir_nro=dir_nro_2,
                                dir_localidad=dir_localidad_2,
                                dir_provincia=dir_provincia_2,
                                dir_area_tel=dir_area_tel_2,
                                dir_telefono=dir_telefono_2,
                                dir_obs=dir_obs_2,
                                dir_tipoenvio=dir_tipoenvio_2,
                                dir_tipocorreo=2,
                            )
                        direcciones.save()
                        messages.success(request,'Se ha agregado la Dirección de Entrega correctamente!')
                    else:
                        #UPDATE
                        print("Oca Retiro en sucursal Actualizada")
                        direcciones = AccountDirecciones.objects.get(dir_id=dir_id_2)
                        direcciones.dir_id = dir_id_2
                        direcciones.dir_nombre = dir_nombre_2
                        direcciones.dir_calle = dir_calle_2
                        direcciones.dir_cp = dir_cp_2
                        direcciones.dir_nro = dir_nro_2
                        direcciones.dir_provincia = dir_provincia_2
                        direcciones.dir_localidad = dir_localidad_2
                        direcciones.dir_area_tel = dir_area_tel_2
                        direcciones.dir_telefono = dir_telefono_2
                        direcciones.dir_obs = dir_obs_2
                        direcciones.dir_tipocorreo = dir_tipocorreo_2   #Entrega en Sucursal (2)
                        direcciones.dir_correo = dir_correo             #OCA (1)
                        direcciones.dir_tipoenvio = 0                   # no tiene Clasico , Express (0)
                        direcciones.save()
                    
                        messages.success(request,'Se ha actualizado la Dirección de Entrega correctamente!')
        if button_press=='delete_oca_ed':
            dir_id_1= request.POST["dir_id_1"]     
            
            direcciones = AccountDirecciones.objects.filter(dir_id=dir_id_1).first()
            if direcciones:
                direcciones.delete()
                messages.success(request,'Se ha eliminado la Dirección de Entrega correctamente!')         
        if button_press=='delete_oca_rs':
            dir_id_2 = request.POST.get('dir_id_2')
            print("delete Retiro sucursar Oca",dir_id_2)
            direcciones = AccountDirecciones.objects.filter(dir_id=dir_id_2).first()
            if direcciones:
                direcciones.delete()
                messages.success(request,'Se ha eliminado la Dirección de Entrega correctamente!')        
        
        #***** CORREO ARGENTINO *************
        if button_press=='save_ca_ed':
            dir_id = request.POST.get('dir_id',0)
            dir_tipocorreo = request.POST.get('dir_tipocorreo',0)
            dir_tipoenvio = request.POST.get('tipoEnvio',0)     #Tipo Envio
            dir_nombre = request.POST.get('dir_nombre', '')     #Nombre
            dir_cp = request.POST.get('dir_cp', '')             #Código Postal
            dir_calle = request.POST.get('dir_calle', '')       #Calle
            dir_nro = request.POST.get('dir_nro', '')           #Número 
            dir_piso= request.POST.get('dir_piso', '')          #Piso
            dir_depto= request.POST.get('dir_depto', '')        #Departamento
            dir_localidad = request.POST.get('dir_localidad', '')  #Localidad
            dir_provincia = request.POST.get('dir_provincia', '')  #Provincia
            dir_area_tel = request.POST.get('dir_area_tel', '')  #Área de Tel
            dir_telefono = request.POST.get('dir_telefono', '')  #Teléfono
            dir_obs = request.POST.get('dir_obs','')

            if dir_tipocorreo == '1':  #ENVIO A DOMICILIO
                
                if dir_id == "" or dir_id == "0":
                    #ADD NEW
                    print("ADD NEW Direccion Entrega CORREO ARGENTINO")
                    direcciones = AccountDirecciones(
                            dir_nombre=dir_nombre,
                            user=request.user,
                            dir_cp=dir_cp,
                            dir_calle=dir_calle,
                            dir_nro=dir_nro,
                            dir_piso=dir_piso,
                            dir_depto=dir_depto,
                            dir_localidad=dir_localidad,
                            dir_provincia=dir_provincia,
                            dir_area_tel=dir_area_tel,
                            dir_telefono=dir_telefono,
                            dir_obs=dir_obs,
                            dir_correo = 2,        #Correo Argentino (2)
                            dir_tipoenvio=dir_tipoenvio,
                            dir_tipocorreo=dir_tipocorreo,
                        )
                    direcciones.save()
                    messages.success(request,'Se ha agregado la Dirección de Entrega correctamente!')
                else:
                    #UPDATE
                    
                    
                    direcciones = AccountDirecciones.objects.get(dir_id=dir_id)
                    direcciones.dir_id = dir_id
                    direcciones.dir_nombre = dir_nombre
                    direcciones.dir_cp = dir_cp
                    direcciones.dir_calle = dir_calle
                    direcciones.dir_cp = dir_cp
                    direcciones.dir_nro = dir_nro
                    direcciones.dir_piso = dir_piso
                    direcciones.dir_depto = dir_depto
                    direcciones.dir_provincia = dir_provincia
                    direcciones.dir_localidad = dir_localidad
                    direcciones.dir_area_tel = dir_area_tel
                    direcciones.dir_telefono = dir_telefono
                    direcciones.dir_obs = dir_obs
                    direcciones.dir_tipocorreo = 1   #Envio a Domicilio
                    direcciones.dir_correo = 2        #Correo Argentino (2)
                    direcciones.dir_tipoenvio = dir_tipoenvio        # Clasico , Express
                    direcciones.save()
                    messages.success(request,'Se ha actualizado la Dirección de Entrega correctamente!')
        if button_press=='save_ca_rs':

            dir_id = request.POST.get('dir_id',0)
            dir_tipocorreo = request.POST.get('dir_tipocorreo',0)
            dir_tipoenvio = request.POST.get('tipoEnvio_RS',0)     #Tipo Envio  Clasico / Expreso
            dir_nombre = request.POST.get('dir_nombre', '')     #Nombre
            dir_cp = request.POST.get('dir_cp', '')             #Código Postal
            dir_calle = request.POST.get('dir_calle', '')       #Calle
            dir_nro = request.POST.get('dir_nro', '')           #Número 
            dir_localidad = request.POST.get('dir_localidad', '')  #Localidad
            dir_provincia = request.POST.get('dir_provincia', '')  #Provincia
            dir_area_tel = request.POST.get('dir_area_tel', '')  #Área de Tel
            dir_telefono = request.POST.get('dir_telefono', '')  #Teléfono
            dir_obs = request.POST.get('dir_obs','')

            if dir_tipocorreo == '2':  #ENTREGA SUCURSAL
                if dir_id == "" or dir_id == "0":
                    #ADD NEW
                    direcciones = AccountDirecciones(
                            dir_nombre=dir_nombre,
                            user=request.user,
                            dir_cp=dir_cp,
                            dir_calle=dir_calle,
                            dir_nro=dir_nro,
                            dir_localidad=dir_localidad,
                            dir_provincia=dir_provincia,
                            dir_area_tel=dir_area_tel,
                            dir_telefono=dir_telefono,
                            dir_obs=dir_obs,
                            dir_correo = 2,        #Correo Argentino (2)
                            dir_tipoenvio=dir_tipoenvio,
                            dir_tipocorreo=dir_tipocorreo,
                        )
                    direcciones.save()
                    messages.success(request,'Se ha agregado la Dirección de Entrega correctamente!')
                else:
                    #UPDATE
                    
                    
                    direcciones = AccountDirecciones.objects.get(dir_id=dir_id)
                    direcciones.dir_id = dir_id
                    direcciones.dir_nombre = dir_nombre
                    direcciones.dir_cp = dir_cp
                    direcciones.dir_calle = dir_calle
                    direcciones.dir_cp = dir_cp
                    direcciones.dir_nro = dir_nro
                    direcciones.dir_provincia = dir_provincia
                    direcciones.dir_localidad = dir_localidad
                    direcciones.dir_area_tel = dir_area_tel
                    direcciones.dir_telefono = dir_telefono
                    direcciones.dir_obs = dir_obs
                    direcciones.dir_tipocorreo = dir_tipocorreo     #Retira en Sucursal (2)
                    direcciones.dir_correo = 2                      #Correo Argentino (2)
                    direcciones.dir_tipoenvio = dir_tipoenvio        # Clasico , Express
                    direcciones.save()
                    messages.success(request,'Se ha actualizado la Dirección de Entrega correctamente!')
        if button_press=='delete_ca_ed':
            dir_del_id = request.POST.get("dir_id_del",0)
            print("delete  Entrega Domicilio Correo Argentino",dir_del_id)
            direcciones = AccountDirecciones.objects.filter(dir_id=dir_del_id).first()
            if direcciones:
                direcciones.delete()
                messages.success(request,'Se ha eliminado la Dirección de Entrega correctamente!')
        if button_press=='delete_ca_rs':
            dir_id = request.POST.get('dir_id',0)
            print("delete Retira en Sucursal Correo Argentino",dir_id)
            direcciones = AccountDirecciones.objects.filter(dir_id=dir_id).first()
            if direcciones:
                direcciones.delete()
                messages.success(request,'Se ha eliminado la Dirección de Entrega correctamente!')
        

        #***** RETIRO EN PERSONA *************
        if button_press=='save_rc':
            dir_id = request.POST.get('dir_id',0)
            dir_correo = request.POST.get('dir_correo',0)       #1-OCA / #2-Correo Argentino / #3 Entregaen persona
            dir_tipocorreo = request.POST.get('dir_tipocorreo',0) #1-Envio a Domicilio / #2-Entrega en Sucursal / #0 Entrega Sucursal
            dir_tipoenvio = request.POST.get('tipoEnvio',0)     #Tipo Envio  #1-> Clasico  #2--> Express
            dir_nombre = request.POST.get('dir_nombre', '')     #Nombre
            dir_cp = request.POST.get('dir_cp', '')             #Código Postal
            dir_calle = request.POST.get('dir_calle', '')       #Calle
            dir_nro = request.POST.get('dir_nro', '')           #Número 
            dir_localidad = request.POST.get('dir_localidad', '')  #Localidad
            dir_provincia = request.POST.get('dir_provincia', '')  #Provincia
            dir_area_tel = request.POST.get('dir_area_tel', '')  #Área de Tel
            dir_telefono = request.POST.get('dir_telefono', '')  #Teléfono
            dir_obs = request.POST.get('dir_obs','')

            if dir_correo == '3':  #Retira en Persona
                print("Save datos Retira Cliente ID:",dir_id)
                if dir_id == "" or dir_id == "0":
                    #ADD NEW
                    print("ADD NEW  Retira Cliente ")
                    direcciones = AccountDirecciones(
                            dir_nombre=dir_nombre,
                            user=request.user,
                            dir_cp=dir_cp,
                            dir_calle=dir_calle,
                            dir_nro=dir_nro,
                            dir_localidad=dir_localidad,
                            dir_provincia=dir_provincia,
                            dir_area_tel=dir_area_tel,
                            dir_telefono=dir_telefono,
                            dir_obs=dir_obs,
                            dir_correo = 3,        #Retira en Persona
                            dir_tipoenvio=dir_tipoenvio,
                            dir_tipocorreo=dir_tipocorreo,
                        )
                    direcciones.save()
                    messages.success(request,'Se ha agregado la Dirección de Entrega correctamente!')
                else:
                    #UPDATE
                    print("UPDATE  Retira Cliente ")
                    
                    direcciones = AccountDirecciones.objects.get(dir_id=dir_id)
                    direcciones.dir_id = dir_id
                    direcciones.dir_nombre = dir_nombre
                    direcciones.dir_cp = dir_cp
                    direcciones.dir_calle = dir_calle
                    direcciones.dir_cp = dir_cp
                    direcciones.dir_nro = dir_nro
                    direcciones.dir_provincia = dir_provincia
                    direcciones.dir_localidad = dir_localidad
                    direcciones.dir_area_tel = dir_area_tel
                    direcciones.dir_telefono = dir_telefono
                    direcciones.dir_obs = dir_obs
                    direcciones.dir_tipocorreo = 0   #Retira Cliente
                    direcciones.dir_correo = 3        #Retira en Persona (3)
                    direcciones.dir_tipoenvio = 0       # Clasico , Express
                    direcciones.save()
                    messages.success(request,'Se ha actualizado la Dirección de Entrega correctamente!')
        if button_press=='delete_rc':
            dir_id = request.POST.get('dir_id',0)
            print("Eliminar Retira cliente. Dir:",dir_id)
            direcciones = AccountDirecciones.objects.filter(dir_id=dir_id).first()
            if direcciones:
                direcciones.delete()
                messages.success(request,'Se ha eliminado la Dirección de Entrega correctamente!')

    #***************************   
    #DEVULVO INFO DE DIRECCIONES
    #***************************
    dir_OCA_ED = AccountDirecciones.objects.filter(user=request.user, dir_correo=1,dir_tipocorreo=1).first() # OCA_ENVIO_DOMICILIO
    dir_OCA_RS = AccountDirecciones.objects.filter(user=request.user, dir_correo=1,dir_tipocorreo=2).first() # OCA_RETIRA_SUCURSAL
    dir_CA_ED = AccountDirecciones.objects.filter(user=request.user, dir_correo=2,dir_tipocorreo=1).first() # CORREO ARGENTINO  ENVIO A DOMICILIO
    dir_CA_RS = AccountDirecciones.objects.filter(user=request.user, dir_correo=2,dir_tipocorreo=2).first() # CORREO ARGENTINO  RETIRA SUCURSAL
    dir_RC = AccountDirecciones.objects.filter(user=request.user, dir_correo=3).first()  # RETIRA CLIENTE
    
    print("********* DIRECCIONES ************")
    print(dir_OCA_ED)
    print(dir_OCA_RS)
    print(dir_CA_ED)
    print(dir_CA_RS)
    print(dir_RC)
    print("**********************************")


    context = {
        'dir_OCA_ED': dir_OCA_ED,
        'dir_OCA_RS': dir_OCA_RS,
        'dir_CA_ED': dir_CA_ED,
        'dir_CA_RS':dir_CA_RS,
        'dir_RC': dir_RC,
        }

    return render(request, 'accounts/edit_direcciones.html',context)
@login_required(login_url='login')
def edit_dir_entrega_correo(request,dir_id=None,dir_tipocorreo=None):


    print("edit_dir_entrega_correo")
    if dir_id ==0:
        messages.warning(request, 'Complete los datos')
        direccion = AccountDirecciones.objects.filter(user=request.user).first()
        direcciones = AccountDirecciones.objects.filter(user=request.user)

        context = {
            'direccion' : direccion,
            'direcciones': direcciones,
        }
    else:
        
        direcciones = AccountDirecciones.objects.filter(dir_id=dir_id).first()
        if direcciones:
            
            #UPDATE DIRECCION
            direcciones = AccountDirecciones(
                    dir_id=dir_id ,
                    dir_nombre=direcciones.dir_nombre,
                    user=request.user,
                    dir_cp=direcciones.dir_cp,
                    dir_calle=direcciones.dir_calle,
                    dir_nro=direcciones.dir_nro,
                    dir_localidad=direcciones.dir_localidad,
                    dir_provincia=direcciones.dir_provincia,
                    dir_telefono=direcciones.dir_telefono,
                    dir_obs=direcciones.dir_obs,
                    dir_tipocorreo=dir_tipocorreo,
                )
            direcciones.save()
            messages.success(request, 'Direccion actualizada con éxito.')
        
        direccion = AccountDirecciones.objects.get(user=request.user,dir_id=dir_id)
        direcciones = AccountDirecciones.objects.filter(user=request.user)

        context = {
            'direccion' : direccion,
            'direcciones': direcciones,
            }
    return render(request, 'accounts/edit_direcciones.html',context)    

@login_required(login_url='login')
def del_dir_entrega(request,dir_id_del=None):

  
    direcciones = AccountDirecciones.objects.filter(dir_id=dir_id_del).first()
    if direcciones:
        direcciones.delete()
        messages.success(request,'Se ha eliminado la Dirección de Entrega correctamente!')