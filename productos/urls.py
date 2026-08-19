from django.urls import path

from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.home, name='home'),
    path('index.html', views.home, name='home_html'),
    path('catalogo.html', views.catalogo, name='catalogo'),
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/categorias/', views.api_categorias, name='api_categorias'),
]
