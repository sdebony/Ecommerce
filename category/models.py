from django.db import models
from django.urls import reverse

# Create your models here.

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['category_name',]

    def get_url(self):
            return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.category_name
    
    def category_name_lower(self):
        return self.category_name.lower()

class SubCategory(models.Model):
    
    
    subcategory_name = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False)
    sub_category_slug = models.SlugField(max_length=100)
    sub_category_description = models.TextField(max_length=255, blank=True)
  
    class Meta:
        verbose_name = 'Sub Category'
        verbose_name_plural = 'Sub Categories'
        ordering = ['subcategory_name',]

    def get_url(self):
            return reverse('products_by_subcategory', args=[self.sub_category_slug])

    def __str__(self):
        return self.subcategory_name
    
    def category_name_lower(self):
        return self.subcategory_name.lower()
