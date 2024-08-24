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

    if request.method=='GET':

        dir_sucursal = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=1).first() # Direccion de Sucursal
        dir_envios = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=2).first() # Direccion de envio
        dir_retiro = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=3).first() # Direccion de envio
        
        context = {
            'dir_sucursal': dir_sucursal,
            'dir_envios': dir_envios,
            'dir_retiro': dir_retiro,
            }

        return render(request, 'accounts/edit_direcciones.html',context)

    if request.method=='POST':

        action = request.POST.get('action')
        if action == 'save':

            dir_id= request.POST["dir_id"]
            dir_nombre= request.POST["dir_nombre"]
            dir_cp= request.POST["dir_cp"]
            dir_calle= request.POST["dir_calle"]
            dir_nro= request.POST["dir_nro"]
            dir_localidad= request.POST["dir_localidad"]
            dir_provincia= request.POST["dir_provincia"]
            dir_telefono= request.POST["dir_telefono"]
            dir_obs= request.POST["dir_obs"]
            dir_area_tel= request.POST["dir_area_tel"]
            dir_tipocorreo= request.POST["dir_tipocorreo"]
            dir_tipoenvio = request.POST.get("tipoEnvio")

            if not dir_id:
                dir_id = "0"

            if dir_id == "0":
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
                        dir_tipoenvio=dir_tipoenvio,
                        dir_tipocorreo=dir_tipocorreo,
                    )
                direcciones.save()
                dir_id=direcciones.dir_id
                messages.success(request, 'Direccion agregada con èxito.')
            
            else:
                
                direcciones = AccountDirecciones.objects.filter(dir_id=dir_id).first()
                if direcciones:
                
                    #UPDATE DIRECCION
                    direcciones = AccountDirecciones(
                            dir_id=dir_id ,
                            user=request.user,
                            dir_nombre=dir_nombre,
                            dir_cp=dir_cp,
                            dir_calle=dir_calle,
                            dir_nro=dir_nro,
                            dir_localidad=dir_localidad,
                            dir_provincia=dir_provincia,
                            dir_area_tel=dir_area_tel,
                            dir_telefono=dir_telefono,
                            dir_obs=dir_obs,
                            dir_tipoenvio=dir_tipoenvio,
                            dir_tipocorreo=dir_tipocorreo,
                        )
                    direcciones.save()
                    messages.success(request, 'Direccion agregada con èxito.')
        elif action == "delete":
            #DELETE DIRECCION
            dir_id_del= request.POST["dir_id_del"]
            if dir_id_del=="":
                dir_id_del="0"
                
            if int(dir_id_del) > 0:
                del_dir_entrega( request,dir_id_del)
            else:
                messages.error(request,'Seleccione una dirección de entrega para eliminarla!')
        
        dir_sucursal = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=1).first() # Direccion de Sucursal
        dir_envios = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=2).first() # Direccion de envio
        dir_retiro = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=3).first() # Direccion de envio
    
        context = {
            'dir_sucursal': dir_sucursal,
            'dir_envios': dir_envios,
            'dir_retiro': dir_retiro,
            }
        return render(request, 'accounts/edit_direcciones.html',context)    


@login_required(login_url='login')
def edit_dir_entrega_correo(request,dir_id=None,dir_tipocorreo=None):

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

#    dir_sucursal = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=1).first() # Direccion de Sucursal
#    dir_envios = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=2).first() # Direccion de envio
#    dir_retiro = AccountDirecciones.objects.filter(user=request.user, dir_tipocorreo=3).first() # Direccion de envio
    
#    context = {
#        'dir_sucursal': dir_sucursal,
#        'dir_envios': dir_envios,
#        'dir_retiro': dir_retiro,
#        }

#    return render(request, 'accounts/edit_direcciones.html',context)   