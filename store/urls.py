from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:subcategory_slug>/', views.store, name='products_by_subcategory'),
    path('categories/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('condiciones', views.condiciones, name='condiciones'),
    path('search-products/', views.search_products, name='search_products'),
    #path('../search/search-products/', views.search_products, name='search_products'),
]
