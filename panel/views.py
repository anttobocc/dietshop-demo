from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from productos.models import Categoria, InventarioSucursal
from sucursales.models import Sucursal
from sucursales.permisos import get_sucursal_activa, set_sucursal_activa, sucursales_permitidas

from .forms import CategoriaForm, InventarioForm, ProductoGlobalForm, SucursalForm, UsuarioCrearForm, UsuarioEditarForm

User = get_user_model()


class PanelLoginView(LoginView):
    template_name = "panel/login.html"
    redirect_authenticated_user = True


class PanelLogoutView(LogoutView):
    next_page = reverse_lazy("panel:login")


@login_required
@require_POST
def sucursal_activa_set(request):
    """Cambia la sucursal con la que trabaja el usuario. Solo acepta sucursales que le están permitidas."""
    permitidas = sucursales_permitidas(request.user)
    sucursal = get_object_or_404(permitidas, pk=request.POST.get("sucursal_id"))
    set_sucursal_activa(request, sucursal)
    return redirect("panel:dashboard")


def _lista_inventarios(sucursal):
    return (
        InventarioSucursal.objects.filter(sucursal=sucursal)
        .select_related("producto", "categoria")
        .order_by("categoria__nombre", "producto__nombre")
    )


@login_required
def dashboard(request):
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return render(request, "panel/sin_sucursal.html")
    return render(request, "panel/dashboard.html", {
        "inventarios": _lista_inventarios(sucursal),
    })


@login_required
def producto_crear(request):
    """Crea un producto nuevo (global) junto con su inventario en la sucursal activa.

    Cualquier usuario autorizado en la sucursal puede crear productos: al no
    existir todavía el producto, no hay riesgo de pisar datos de otra sucursal.
    """
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")

    if request.method == "POST":
        prod_form = ProductoGlobalForm(request.POST, request.FILES)
        inv_form = InventarioForm(request.POST, sucursal=sucursal)
        if prod_form.is_valid() and inv_form.is_valid():
            producto = prod_form.save()
            inventario = inv_form.save(commit=False)
            inventario.producto = producto
            inventario.sucursal = sucursal
            inventario.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect("panel:dashboard")
    else:
        prod_form = ProductoGlobalForm()
        inv_form = InventarioForm(sucursal=sucursal)

    return render(request, "panel/dashboard.html", {
        "inventarios": _lista_inventarios(sucursal),
        "prod_form": prod_form,
        "inv_form": inv_form,
        "modo": "crear",
        "puede_editar_global": True,
    })


@login_required
def producto_editar(request, pk):
    """Edita el inventario de un producto en la sucursal activa.

    Los datos globales del producto (nombre, precio, imagen, tags, activo,
    etc.) solo los puede modificar un superusuario: si no lo es, ni siquiera
    se instancia el formulario de esos campos con el POST recibido, así que
    un formulario manipulado no tiene ningún efecto sobre ellos.
    """
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")

    # Seguridad: el pk pertenece siempre a InventarioSucursal, filtrado por
    # la sucursal activa. Un id de otra sucursal (o inexistente) da 404.
    inventario = get_object_or_404(
        InventarioSucursal.objects.select_related("producto"),
        pk=pk,
        sucursal=sucursal,
    )
    producto = inventario.producto
    puede_editar_global = request.user.is_superuser

    if request.method == "POST":
        inv_form = InventarioForm(request.POST, instance=inventario, sucursal=sucursal)
        prod_form = ProductoGlobalForm(request.POST, request.FILES, instance=producto) if puede_editar_global else None

        inv_ok = inv_form.is_valid()
        prod_ok = prod_form.is_valid() if prod_form else True

        if inv_ok and prod_ok:
            inv_form.save()
            if prod_form:
                prod_form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("panel:dashboard")
    else:
        inv_form = InventarioForm(instance=inventario, sucursal=sucursal)
        prod_form = ProductoGlobalForm(instance=producto) if puede_editar_global else None

    return render(request, "panel/dashboard.html", {
        "inventarios": _lista_inventarios(sucursal),
        "prod_form": prod_form,
        "inv_form": inv_form,
        "modo": "editar",
        "producto": producto,
        "puede_editar_global": puede_editar_global,
    })


@login_required
@require_POST
def producto_eliminar(request, pk):
    """Quita el producto del inventario de la sucursal activa.

    No borra el Producto global: otras sucursales que también lo tengan en
    su inventario no se ven afectadas. Borrar el producto de toda la cadena
    queda fuera del alcance de esta pantalla (sucursal-scoped por diseño).
    """
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")
    inventario = get_object_or_404(InventarioSucursal, pk=pk, sucursal=sucursal)
    nombre = inventario.producto.nombre
    inventario.delete()
    messages.success(request, f'"{nombre}" se quitó del inventario de {sucursal.nombre}.')
    return redirect("panel:dashboard")


@login_required
@require_POST
def producto_toggle_activo(request, pk):
    """Activa/desactiva la disponibilidad del producto en la sucursal activa (no afecta otras sucursales)."""
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")
    inventario = get_object_or_404(InventarioSucursal, pk=pk, sucursal=sucursal)
    inventario.disponible = request.POST.get("activo") == "on"
    inventario.save(update_fields=["disponible"])
    estado = "disponible" if inventario.disponible else "no disponible"
    messages.success(request, f'"{inventario.producto.nombre}" quedó {estado} en {sucursal.nombre}.')
    return redirect("panel:dashboard")


@login_required
def categorias(request):
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")

    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.sucursal = sucursal
            categoria.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm()

    lista = Categoria.objects.filter(sucursal=sucursal).order_by("nombre")
    return render(request, "panel/categorias.html", {"categorias": lista, "form": form})


@login_required
def categoria_editar(request, pk):
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")

    # Seguridad: solo categorías de la sucursal activa. Un id de otra
    # sucursal (o inexistente) da 404, nunca se puede editar por URL manual.
    categoria = get_object_or_404(Categoria, pk=pk, sucursal=sucursal)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, "panel/categoria_form.html", {"form": form, "categoria": categoria})


def _exigir_superusuario(request):
    """Gestión de sucursales: exclusiva del administrador global."""
    if not request.user.is_superuser:
        raise PermissionDenied


@login_required
def sucursales_lista(request):
    _exigir_superusuario(request)
    lista = Sucursal.objects.all().prefetch_related("usuarios").order_by("nombre")
    return render(request, "panel/sucursales.html", {"sucursales": lista, "form": SucursalForm()})


@login_required
def sucursal_crear(request):
    _exigir_superusuario(request)
    if request.method == "POST":
        form = SucursalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sucursal creada correctamente.")
            return redirect("panel:sucursales")
    else:
        form = SucursalForm()
    lista = Sucursal.objects.all().prefetch_related("usuarios").order_by("nombre")
    return render(request, "panel/sucursales.html", {"sucursales": lista, "form": form})


@login_required
def sucursal_editar(request, pk):
    _exigir_superusuario(request)
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == "POST":
        form = SucursalForm(request.POST, instance=sucursal)
        if form.is_valid():
            form.save()
            messages.success(request, "Sucursal actualizada correctamente.")
            return redirect("panel:sucursales")
    else:
        form = SucursalForm(instance=sucursal)
    return render(request, "panel/sucursal_form.html", {"form": form, "sucursal": sucursal})


@login_required
@require_POST
def sucursal_toggle_activo(request, pk):
    """Activa/desactiva una sucursal. Nunca la elimina: los datos históricos quedan intactos."""
    _exigir_superusuario(request)
    sucursal = get_object_or_404(Sucursal, pk=pk)
    sucursal.activo = request.POST.get("activo") == "on"
    sucursal.save(update_fields=["activo"])
    estado = "activada" if sucursal.activo else "desactivada"
    messages.success(request, f'"{sucursal.nombre}" fue {estado}.')
    return redirect("panel:sucursales")


@login_required
def usuarios_lista(request):
    _exigir_superusuario(request)
    lista = User.objects.filter(is_superuser=False).prefetch_related("sucursales_autorizadas").order_by("username")
    return render(request, "panel/usuarios.html", {"usuarios": lista, "form": UsuarioCrearForm()})


@login_required
def usuario_crear(request):
    _exigir_superusuario(request)
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("panel:usuarios")
    else:
        form = UsuarioCrearForm()
    lista = User.objects.filter(is_superuser=False).prefetch_related("sucursales_autorizadas").order_by("username")
    return render(request, "panel/usuarios.html", {"usuarios": lista, "form": form})


@login_required
def usuario_editar(request, pk):
    _exigir_superusuario(request)
    # Seguridad: excluye superusuarios explícitamente. Un id de superusuario
    # da 404 -- esta pantalla nunca puede tocar una cuenta de administrador.
    usuario = get_object_or_404(User, pk=pk, is_superuser=False)
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("panel:usuarios")
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(request, "panel/usuario_form.html", {"form": form, "usuario": usuario})


@login_required
def usuario_password(request, pk):
    _exigir_superusuario(request)
    usuario = get_object_or_404(User, pk=pk, is_superuser=False)
    if request.method == "POST":
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contraseña de "{usuario.username}" actualizada correctamente.')
            return redirect("panel:usuarios")
    else:
        form = SetPasswordForm(usuario)
    return render(request, "panel/usuario_password.html", {"form": form, "usuario": usuario})


@login_required
@require_POST
def usuario_toggle_activo(request, pk):
    """Activa/desactiva el usuario (is_active). No lo elimina."""
    _exigir_superusuario(request)
    usuario = get_object_or_404(User, pk=pk, is_superuser=False)
    usuario.is_active = request.POST.get("activo") == "on"
    usuario.save(update_fields=["is_active"])
    estado = "activado" if usuario.is_active else "desactivado"
    messages.success(request, f'"{usuario.username}" fue {estado}.')
    return redirect("panel:usuarios")
