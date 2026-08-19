from django.contrib import admin

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "fecha_creacion")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "stock", "activo", "destacado", "oferta")
    list_filter = ("categoria", "activo", "destacado", "oferta")
    search_fields = ("nombre", "descripcion")
