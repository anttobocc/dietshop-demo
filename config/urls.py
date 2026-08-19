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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('panel.urls')),
    path('', include('productos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    # Sirve los archivos originales del frontend (script.js, styles.css, assets/)
    # directamente desde la raíz del proyecto, sin moverlos ni duplicarlos.
    urlpatterns += [
        path('script.js', serve_static, {'document_root': settings.BASE_DIR, 'path': 'script.js'}),
        path('styles.css', serve_static, {'document_root': settings.BASE_DIR, 'path': 'styles.css'}),
        re_path(r'^assets/(?P<path>.*)$', serve_static, {'document_root': settings.BASE_DIR / 'assets'}),
    ]
