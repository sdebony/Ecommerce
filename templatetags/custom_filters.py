from django import template
import locale

register = template.Library()

@register.filter
def currency_format(value):
    locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')  # Configura la localización a Argentina
    return locale.currency(value, symbol=True, grouping=True)
