from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse

from sucursales.models import Sucursal

from .models import Categoria, InventarioSucursal


def home(request):
    """Sirve index.html tal cual está en disco (bytes exactos, sin normalizar saltos de linea)."""
    html = (Path(settings.BASE_DIR) / "index.html").read_bytes()
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def catalogo(request):
    """Sirve catalogo.html tal cual está en disco (bytes exactos, sin normalizar saltos de linea)."""
    html = (Path(settings.BASE_DIR) / "catalogo.html").read_bytes()
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def _resolver_sucursal_publica(request):
    """
    Resuelve la sucursal del catálogo público a partir de ?sucursal=<id>.

    Es independiente del sistema de permisos del panel (sucursales.permisos):
    el catálogo público no requiere login y cualquier visitante puede elegir
    cualquier sucursal activa, así que acá NO se usan sucursales_permitidas()
    ni get_sucursal_activa().

    Devuelve (sucursal, error): si `sucursal` es None, `error` ya es un
    JsonResponse listo para devolver tal cual.
    """
    sucursal_id = request.GET.get("sucursal")

    if sucursal_id:
        try:
            sucursal_id = int(sucursal_id)
        except ValueError:
            return None, JsonResponse({"error": "El parámetro 'sucursal' debe ser un número."}, status=400)
        sucursal = Sucursal.objects.filter(pk=sucursal_id, activo=True).first()
        if sucursal is None:
            # Nunca se cae silenciosamente a otra sucursal: si piden una
            # sucursal puntual y no es válida, se informa el error.
            return None, JsonResponse({"error": "La sucursal solicitada no existe o no está activa."}, status=404)
        return sucursal, None

    # Sin parámetro: sucursal por defecto. Se identifica por nombre (no por
    # id hardcodeado), que es la misma convención ya usada por la migración
    # de datos que creó "Sucursal Central" en la etapa 1.
    sucursal = Sucursal.objects.filter(activo=True, nombre="Sucursal Central").first()
    if sucursal is None:
        activas = Sucursal.objects.filter(activo=True)
        if activas.count() == 1:
            sucursal = activas.first()
    if sucursal is None:
        return None, JsonResponse(
            {"error": "No se pudo determinar una sucursal por defecto. Especificá '?sucursal=<id>'."},
            status=400,
        )
    return sucursal, None


def _producto_json(inventario):
    producto = inventario.producto
    return {
        "id": producto.id,
        "name": producto.nombre,
        "price": float(producto.precio),
        "oldPrice": float(producto.precio_anterior) if producto.precio_anterior else None,
        "category": inventario.categoria.nombre,
        "description": producto.descripcion,
        "image": producto.imagen.url if producto.imagen else None,
        "tags": [tag for tag in producto.tags.split(",") if tag],
        "stock": inventario.stock,
        "destacado": producto.destacado,
        "nuevo": producto.nuevo,
        "oferta": producto.oferta,
    }


def api_productos(request):
    """Productos disponibles en la sucursal pedida (o la sucursal por defecto)."""
    sucursal, error = _resolver_sucursal_publica(request)
    if error:
        return error
    inventarios = (
        InventarioSucursal.objects.filter(sucursal=sucursal, disponible=True, producto__activo=True)
        .select_related("producto", "categoria")
    )
    return JsonResponse([_producto_json(inventario) for inventario in inventarios], safe=False)


def api_categorias(request):
    """Categorías activas de la sucursal pedida (o la sucursal por defecto)."""
    sucursal, error = _resolver_sucursal_publica(request)
    if error:
        return error
    categorias = Categoria.objects.filter(sucursal=sucursal, activo=True)
    data = [
        {"id": categoria.id, "name": categoria.nombre, "description": categoria.descripcion}
        for categoria in categorias
    ]
    return JsonResponse(data, safe=False)


def api_sucursales(request):
    """Sucursales activas, visibles públicamente (sin autenticación)."""
    sucursales = Sucursal.objects.filter(activo=True).order_by("nombre")
    data = [
        {"id": sucursal.id, "name": sucursal.nombre, "address": sucursal.direccion}
        for sucursal in sucursales
    ]
    return JsonResponse(data, safe=False)
