from .models import Category

#Agregar en settings en la parte de templates la ruta
def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)
