from .models import Category,SubCategory

def menu_links(request):
    links = Category.objects.all().order_by('orden')
    sub_links = SubCategory.objects.all().order_by('orden')
    return dict(links=links,sub_links=sub_links)
