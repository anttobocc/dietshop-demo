from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse

from .models import Categoria, Producto


def home(request):
    """Sirve index.html tal cual está en disco (bytes exactos, sin normalizar saltos de linea)."""
    html = (Path(settings.BASE_DIR) / "index.html").read_bytes()
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def catalogo(request):
    """Sirve catalogo.html tal cual está en disco (bytes exactos, sin normalizar saltos de linea)."""
    html = (Path(settings.BASE_DIR) / "catalogo.html").read_bytes()
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def _producto_json(producto):
    return {
        "id": producto.id,
        "name": producto.nombre,
        "price": float(producto.precio),
        "oldPrice": float(producto.precio_anterior) if producto.precio_anterior else None,
        "category": producto.categoria.nombre,
        "description": producto.descripcion,
        "image": producto.imagen.url if producto.imagen else None,
        "tags": [tag for tag in producto.tags.split(",") if tag],
        "stock": producto.stock,
        "destacado": producto.destacado,
        "nuevo": producto.nuevo,
        "oferta": producto.oferta,
    }


def api_productos(request):
    """Devuelve los productos activos con la forma que ya espera script.js."""
    productos = Producto.objects.filter(activo=True).select_related("categoria")
    return JsonResponse([_producto_json(producto) for producto in productos], safe=False)


def api_categorias(request):
    """Devuelve las categorías activas."""
    categorias = Categoria.objects.filter(activo=True)
    data = [
        {"id": categoria.id, "name": categoria.nombre, "description": categoria.descripcion}
        for categoria in categorias
    ]
    return JsonResponse(data, safe=False)
