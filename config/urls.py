"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_static


def _serve_sin_cache(request, **kwargs):
    """
    Igual que serve_static, pero sin permitir que el navegador guarde una
    copia vieja: mientras se esta iterando sobre script.js/styles.css en
    desarrollo, un script.js cacheado (el navegador puede cachearlo por
    heuristica al traer Last-Modified sin Cache-Control) haria que una
    correccion ya aplicada en el archivo pareciera "no funcionar".
    """
    response = serve_static(request, **kwargs)
    response["Cache-Control"] = "no-store"
    return response


def _serve_media(request, **kwargs):
    """
    Igual que serve_static, pero con un Cache-Control acotado (1 hora) para
    que navegar Inicio/Catalogo/Ofertas/Categorias de un lado a otro no
    vuelva a descargar las mismas fotos de producto cada vez. No es un
    cache "eterno": productos/management/commands/importar_productos.py
    puede sobreescribir el mismo nombre de archivo con otro contenido (si
    se reemplaza una imagen en assets/ y se vuelve a correr el comando), asi
    que must-revalidate obliga a chequear con el servidor pasada la hora en
    vez de confiar en la copia vieja indefinidamente.
    """
    response = serve_static(request, **kwargs)
    response["Cache-Control"] = "public, max-age=3600, must-revalidate"
    return response


urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('panel.urls')),
    path('', include('productos.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', _serve_media, {'document_root': settings.MEDIA_ROOT}),
        # Igual que script.js/styles.css mas abajo: sin esto, panel.css puede
        # quedar cacheado por heuristica y una correccion recien aplicada
        # (por ejemplo al centrado de los modales) parece "no funcionar".
        re_path(r'^static/(?P<path>.*)$', _serve_sin_cache, {'document_root': settings.STATICFILES_DIRS[0]}),
    ]
    # Sirve los archivos originales del frontend (script.js, styles.css, assets/)
    # directamente desde la raíz del proyecto, sin moverlos ni duplicarlos.
    urlpatterns += [
        path('script.js', _serve_sin_cache, {'document_root': settings.BASE_DIR, 'path': 'script.js'}),
        path('styles.css', _serve_sin_cache, {'document_root': settings.BASE_DIR, 'path': 'styles.css'}),
        re_path(r'^assets/(?P<path>.*)$', serve_static, {'document_root': settings.BASE_DIR / 'assets'}),
    ]
