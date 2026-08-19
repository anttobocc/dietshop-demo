"""
Helpers de permisos por sucursal.

La sucursal "activa" de un usuario se guarda en sesión, pero SIEMPRE se
revalida contra las sucursales realmente permitidas para ese usuario en
cada request — nunca se confía ciegamente en el valor guardado en sesión.
"""
from django.core.exceptions import PermissionDenied

from .models import Sucursal

SESSION_KEY = "sucursal_activa_id"


def sucursales_permitidas(user):
    """Sucursales activas que el usuario puede usar. Superusuario: todas."""
    if user.is_superuser:
        return Sucursal.objects.filter(activo=True)
    return user.sucursales_autorizadas.filter(activo=True)


def get_sucursal_activa(request):
    """
    Devuelve la Sucursal con la que el usuario está trabajando ahora mismo,
    o None si todavía no hay ninguna resuelta (sin permisos, o con varias
    sucursales permitidas y sin selección explícita).
    """
    permitidas = sucursales_permitidas(request.user)
    sucursal_id = request.session.get(SESSION_KEY)

    if sucursal_id:
        sucursal = permitidas.filter(pk=sucursal_id).first()
        if sucursal:
            return sucursal
        # La sucursal guardada ya no es válida (desactivada, o el usuario
        # perdió el acceso) -> se descarta y se vuelve a resolver.
        del request.session[SESSION_KEY]

    if permitidas.count() == 1:
        sucursal = permitidas.first()
        request.session[SESSION_KEY] = sucursal.pk
        return sucursal

    return None


def set_sucursal_activa(request, sucursal):
    """Guarda `sucursal` como activa, validando primero que esté permitida."""
    permitidas = sucursales_permitidas(request.user)
    if not permitidas.filter(pk=sucursal.pk).exists():
        raise PermissionDenied("El usuario no tiene acceso a esa sucursal.")
    request.session[SESSION_KEY] = sucursal.pk
