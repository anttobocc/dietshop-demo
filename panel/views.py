from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from productos.models import Categoria, Producto

from .forms import CategoriaForm, ProductoForm


class PanelLoginView(LoginView):
    template_name = "panel/login.html"
    redirect_authenticated_user = True


class PanelLogoutView(LogoutView):
    next_page = reverse_lazy("panel:login")


def _lista_productos():
    return Producto.objects.select_related("categoria").order_by("categoria__nombre", "nombre")


@login_required
def dashboard(request):
    return render(request, "panel/dashboard.html", {"productos": _lista_productos()})


@login_required
def producto_crear(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect("panel:dashboard")
    else:
        form = ProductoForm()
    return render(request, "panel/dashboard.html", {
        "productos": _lista_productos(),
        "form": form,
        "modo": "crear",
    })


@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("panel:dashboard")
    else:
        form = ProductoForm(instance=producto)
    return render(request, "panel/dashboard.html", {
        "productos": _lista_productos(),
        "form": form,
        "modo": "editar",
        "producto": producto,
    })


@login_required
@require_POST
def producto_eliminar(request, pk):
    """Elimina el producto definitivamente. Se confirma con un modal en el propio dashboard."""
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    messages.success(request, "Producto eliminado definitivamente.")
    return redirect("panel:dashboard")


@login_required
@require_POST
def producto_toggle_activo(request, pk):
    """Activa/desactiva un producto sin borrarlo (checkbox de la tabla)."""
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = request.POST.get("activo") == "on"
    producto.save(update_fields=["activo"])
    estado = "activado" if producto.activo else "desactivado"
    messages.success(request, f'"{producto.nombre}" fue {estado}.')
    return redirect("panel:dashboard")


@login_required
def categorias(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm()
    lista = Categoria.objects.all().order_by("nombre")
    return render(request, "panel/categorias.html", {"categorias": lista, "form": form})


@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, "panel/categoria_form.html", {"form": form, "categoria": categoria})
