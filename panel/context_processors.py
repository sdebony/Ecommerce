from .models import Alerta  # Ajusta la importación según tu modelo
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import AccountPermition
from django.http import JsonResponse
from panel.views import panel_verificar_alertas

def alertas_context_processor(request):
    

    if request.user.is_authenticated:
        if settings.ACTIVAR_ALERTAS == 'SI':
            panel_verificar_alertas(request)
            alertas = Alerta.objects.filter(usuario=request.user, leido=False)
            cant_alertas = alertas.count()
        else:
            alertas = []
            cant_alertas = 0
    else:
        alertas = []
        cant_alertas = 0

    return {
        'alertas': alertas,
        'cant_alertas': cant_alertas,
    }

    
