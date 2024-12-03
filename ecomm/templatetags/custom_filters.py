from django import template
from datetime import datetime

import locale

register = template.Library()

# Agregar en el HTML el {% load custom_filters %}
#  

@register.filter
def decimal_point(value):
    """
    Convierte comas en puntos decimales en los números.
    """
    if isinstance(value, float):
        return str(value).replace(',', '.')
    elif isinstance(value, str):
        return value.replace(',', '.')
    return value

@register.filter
def format_currency(value):
    """
    Formatea un número en formato de moneda.
    Ejemplo: 12345678.90 se convierte en $12,345,678.90
    """
    try:
        locale.setlocale(locale.LC_ALL, '')
        return locale.currency(value, grouping=True)
    except (ValueError, TypeError):
        return value

@register.filter
def format_currency_usd(value):
    
    try:
        # Formato con separadores de miles
        formatted_value = "{:,.2f}".format(value)
        return f"USD {formatted_value}"
    except (ValueError, TypeError):
        return value

@register.filter
def format_currency_def(value):
    
    try:
        # Formato con separadores de miles
        formatted_value = "{:,.2f}".format(value)
        return f"{formatted_value}"
    except (ValueError, TypeError):
        return value

@register.filter
def format_integer_def(value):
    try:
        # Formato con separadores de miles sin decimales
        formatted_value = "{:,.0f}".format(value)
        return f"{formatted_value}"
    except (ValueError, TypeError):
        return value

@register.filter
def format_number(value):
    try:
        # Formato con separadores de miles sin decimales
        formatted_value = "{:,.2f}".format(value)
        return f"{formatted_value}"
    except (ValueError, TypeError):
        return value

@register.filter
def format_iso_date(value):
    try:
        return datetime.fromisoformat(value.split(".")[0]).strftime('%d-%m-%Y')
    except Exception:
        return value  # Devuelve la fecha original si hay un error