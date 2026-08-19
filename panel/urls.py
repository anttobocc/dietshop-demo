from django.urls import path

from . import views

app_name = 'panel'

urlpatterns = [
    path('login/', views.PanelLoginView.as_view(), name='login'),
    path('logout/', views.PanelLogoutView.as_view(), name='logout'),
    path('sucursal-activa/', views.sucursal_activa_set, name='sucursal_activa'),
    path('', views.dashboard, name='dashboard'),
    path('productos/nuevo/', views.producto_crear, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),
    path('productos/<int:pk>/activo/', views.producto_toggle_activo, name='producto_toggle_activo'),
    path('categorias/', views.categorias, name='categorias'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('sucursales/', views.sucursales_lista, name='sucursales'),
    path('sucursales/nueva/', views.sucursal_crear, name='sucursal_crear'),
    path('sucursales/<int:pk>/editar/', views.sucursal_editar, name='sucursal_editar'),
    path('sucursales/<int:pk>/activo/', views.sucursal_toggle_activo, name='sucursal_toggle_activo'),
    path('usuarios/', views.usuarios_lista, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/password/', views.usuario_password, name='usuario_password'),
    path('usuarios/<int:pk>/activo/', views.usuario_toggle_activo, name='usuario_toggle_activo'),
]
