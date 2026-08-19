from django.contrib import admin

from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "activo", "fecha_creacion")
    list_filter = ("activo",)
    search_fields = ("nombre",)
    filter_horizontal = ("usuarios",)
