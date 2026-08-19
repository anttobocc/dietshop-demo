from .permisos import get_sucursal_activa, sucursales_permitidas


def sucursal_activa(request):
    """Inyecta la sucursal activa y las disponibles en los templates del panel."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not request.path.startswith("/panel/"):
        return {}
    return {
        "sucursal_activa": get_sucursal_activa(request),
        "sucursales_disponibles": sucursales_permitidas(user),
    }
