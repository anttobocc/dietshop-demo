from django.contrib import admin

from .models import Categoria, InventarioSucursal, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "fecha_creacion")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "activo", "destacado", "oferta")
    list_filter = ("activo", "destacado", "oferta")
    search_fields = ("nombre", "descripcion")


@admin.register(InventarioSucursal)
class InventarioSucursalAdmin(admin.ModelAdmin):
    list_display = ("producto", "sucursal", "categoria", "stock", "disponible")
    list_filter = ("sucursal", "categoria", "disponible")
    search_fields = ("producto__nombre",)
