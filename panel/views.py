from functools import partial

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from productos.models import Categoria, InventarioSucursal
from sucursales.models import Sucursal
from sucursales.permisos import get_sucursal_activa, set_sucursal_activa, sucursales_permitidas

from .forms import (
    CategoriaForm,
    InventarioForm,
    ProductoGlobalForm,
    SucursalForm,
    SucursalInicializarForm,
    UsuarioCrearForm,
    UsuarioEditarForm,
)

User = get_user_model()


def _adjuntar_form_edicion(lista, form_class, prefijo, pk_error=None, form_con_error=None):
    """Le agrega a cada objeto de `lista` un `.edit_form` (instancia de
    `form_class` ligada a ese objeto) para el modal de edicion inline de
    categorias.html/sucursales.html/usuarios.html. `auto_id` queda
    namespaced por objeto (ej. "cat3_id_nombre") porque los modales de
    todas las filas conviven ocultos en la misma pagina -- sin esto, los
    id="id_nombre" se repetirian y las <label for="..."> quedarian
    ambiguas.

    Si `pk_error`/`form_con_error` vienen dados (POST invalido al editar
    ese objeto puntual), a ESE objeto se le adjunta el form ya bindeado
    -con sus errores- en vez de uno fresco, y `.modal_forzado_abierto=True`
    para que el template fuerce ese modal abierto en el primer render
    (en vez de perder los errores en una pagina aparte)."""
    for obj in lista:
        if pk_error is not None and obj.pk == pk_error and form_con_error is not None:
            obj.edit_form = form_con_error
            obj.modal_forzado_abierto = True
        else:
            obj.edit_form = form_class(instance=obj, auto_id=f"{prefijo}{obj.pk}_%s")
            obj.modal_forzado_abierto = False
    return lista


def _adjuntar_form_password(lista, prefijo, pk_error=None, form_con_error=None):
    """Igual que `_adjuntar_form_edicion` pero para el modal de "Cambiar
    contraseña" (SetPasswordForm, que no es un ModelForm asi que necesita
    su propio helper -- se instancia con el usuario como primer argumento
    posicional, no con `instance=`)."""
    for obj in lista:
        if pk_error is not None and obj.pk == pk_error and form_con_error is not None:
            obj.password_form = form_con_error
            obj.password_modal_forzado_abierto = True
        else:
            obj.password_form = SetPasswordForm(obj, auto_id=f"{prefijo}{obj.pk}_%s")
            obj.password_modal_forzado_abierto = False
    return lista


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
        # El precio lo puede editar cualquier usuario autorizado en la
        # sucursal; el resto de los datos globales (nombre, descripcion,
        # imagen, activo/destacado/nuevo/oferta) siguen siendo exclusivos
        # del superusuario -- ver ProductoGlobalForm.solo_precio.
        prod_form = ProductoGlobalForm(request.POST, request.FILES, instance=producto, solo_precio=not puede_editar_global)

        inv_ok = inv_form.is_valid()
        prod_ok = prod_form.is_valid()

        if inv_ok and prod_ok:
            inv_form.save()
            prod_form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("panel:dashboard")
    else:
        inv_form = InventarioForm(instance=inventario, sucursal=sucursal)
        prod_form = ProductoGlobalForm(instance=producto, solo_precio=not puede_editar_global)

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
    _adjuntar_form_edicion(lista, CategoriaForm, "cat")
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
        # Invalido: en vez de mandar a la pagina standalone (perdiendo el
        # contexto de "estaba editando desde el modal"), se vuelve a la
        # lista con ESE modal forzado abierto y los errores visibles.
        lista = Categoria.objects.filter(sucursal=sucursal).order_by("nombre")
        _adjuntar_form_edicion(lista, CategoriaForm, "cat", pk_error=categoria.pk, form_con_error=form)
        return render(request, "panel/categorias.html", {"categorias": lista, "form": CategoriaForm()})
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, "panel/categoria_form.html", {"form": form, "categoria": categoria})


@login_required
@require_POST
def categoria_toggle_activo(request, pk):
    """Activa/desactiva una categoría directamente desde la lista (mismo
    mecanismo que sucursal_toggle_activo/usuario_toggle_activo)."""
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")
    categoria = get_object_or_404(Categoria, pk=pk, sucursal=sucursal)
    categoria.activo = request.POST.get("activo") == "on"
    categoria.save(update_fields=["activo"])
    estado = "activada" if categoria.activo else "desactivada"
    messages.success(request, f'"{categoria.nombre}" fue {estado}.')
    return redirect("panel:categorias")


@login_required
@require_POST
def categoria_eliminar(request, pk):
    """Elimina definitivamente una categoría de la sucursal activa. Mismos
    permisos que crear/editar categorías (cualquier usuario autorizado en
    la sucursal, no solo superusuario).

    InventarioSucursal.categoria es on_delete=PROTECT (ver
    productos/models.py): si la categoría todavía tiene productos
    cargados, Django levanta ProtectedError en vez de borrar en cascada --
    se captura y se le muestra al usuario un mensaje claro en vez de una
    página de error técnica, igual que sucursal_eliminar.
    """
    sucursal = get_sucursal_activa(request)
    if sucursal is None:
        return redirect("panel:dashboard")
    # Seguridad: solo categorías de la sucursal activa, igual que categoria_editar.
    categoria = get_object_or_404(Categoria, pk=pk, sucursal=sucursal)
    nombre = categoria.nombre
    try:
        categoria.delete()
    except ProtectedError:
        messages.error(
            request,
            f'No se pudo eliminar "{nombre}": todavía tiene productos cargados. '
            "Quitá primero esos productos (o desactivala en vez de eliminarla) e intentá de nuevo.",
        )
        return redirect("panel:categorias")
    messages.success(request, f'"{nombre}" fue eliminada.')
    return redirect("panel:categorias")


def _exigir_superusuario(request):
    """Gestión de sucursales: exclusiva del administrador global."""
    if not request.user.is_superuser:
        raise PermissionDenied


def _lista_sucursales_con_forms(**kwargs_edicion):
    """Sucursales + `.edit_form` (modal de editar) y `.inicializar_form`/
    `.tiene_inventario` (modal de "Inicializar productos") adjuntados.
    `kwargs_edicion` se reenvia a `_adjuntar_form_edicion` (pk_error/
    form_con_error si el modal de EDITAR de una sucursal esta invalido).

    El modal de editar tampoco muestra "activa" (ocultar_activo=True): el
    estado solo se cambia desde el switch de la lista, igual que
    categorías/usuarios."""
    lista = Sucursal.objects.all().prefetch_related("usuarios").order_by("nombre")
    _adjuntar_form_edicion(lista, partial(SucursalForm, ocultar_activo=True), "suc", **kwargs_edicion)
    for s in lista:
        s.tiene_inventario = InventarioSucursal.objects.filter(sucursal=s).exists()
        s.inicializar_form = None if s.tiene_inventario else SucursalInicializarForm(destino=s, auto_id=f"init{s.pk}_%s")
    return lista


@login_required
def sucursales_lista(request):
    _exigir_superusuario(request)
    lista = _lista_sucursales_con_forms()
    return render(request, "panel/sucursales.html", {"sucursales": lista, "form": SucursalForm(ocultar_activo=True)})


@login_required
def sucursal_crear(request):
    _exigir_superusuario(request)
    if request.method == "POST":
        # ocultar_activo=True: "activa" no se pide al crear (Sucursal.activo
        # ya tiene default=True en el modelo).
        form = SucursalForm(request.POST, ocultar_activo=True)
        if form.is_valid():
            form.save()
            messages.success(request, "Sucursal creada correctamente.")
            return redirect("panel:sucursales")
    else:
        form = SucursalForm(ocultar_activo=True)
    lista = _lista_sucursales_con_forms()
    return render(request, "panel/sucursales.html", {"sucursales": lista, "form": form})


@login_required
def sucursal_editar(request, pk):
    _exigir_superusuario(request)
    sucursal = get_object_or_404(Sucursal, pk=pk)
    if request.method == "POST":
        # ocultar_activo=True: el estado no se edita desde este formulario,
        # solo desde el switch de la lista (ver sucursal_toggle_activo) --
        # un POST manipulado con "activo" tampoco tendría efecto.
        form = SucursalForm(request.POST, instance=sucursal, ocultar_activo=True)
        if form.is_valid():
            form.save()
            messages.success(request, "Sucursal actualizada correctamente.")
            return redirect("panel:sucursales")
        # Invalido: igual que categoria_editar, se vuelve a la lista con
        # el modal de ESTA sucursal forzado abierto y los errores visibles.
        lista = _lista_sucursales_con_forms(pk_error=sucursal.pk, form_con_error=form)
        return render(request, "panel/sucursales.html", {"sucursales": lista, "form": SucursalForm(ocultar_activo=True)})
    else:
        form = SucursalForm(instance=sucursal, ocultar_activo=True)
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
@require_POST
def sucursal_eliminar(request, pk):
    """Elimina definitivamente una sucursal y TODO lo que le pertenece
    exclusivamente a ella. Solo superusuario (misma restriccion que el
    resto de la gestion de sucursales).

    Categoria.sucursal e InventarioSucursal.sucursal/categoria son
    on_delete=PROTECT (ver productos/models.py) -- en vez de dejar que
    Django tire ProtectedError, se borra explicitamente en el orden
    correcto dentro de una transaccion:
      1. InventarioSucursal de esta sucursal (deja de haber referencias
         PROTECT tanto a la sucursal como a sus categorias).
      2. Categoria de esta sucursal (ya sin inventario que las proteja).
      3. La Sucursal misma. Esto tambien limpia automaticamente la tabla
         intermedia de Sucursal.usuarios (M2M): a los usuarios se les
         quita el acceso a esta sucursal, pero el usuario en si NUNCA se
         toca (borrar filas de un M2M no borra los objetos relacionados).

    Producto es global (no pertenece a una sucursal) e InventarioSucursal
    apunta A Producto con on_delete=CASCADE, no al reves -- borrar el
    inventario de esta sucursal jamas borra el Producto, sin importar si
    otras sucursales lo siguen usando o no.
    """
    _exigir_superusuario(request)
    sucursal = get_object_or_404(Sucursal, pk=pk)
    nombre = sucursal.nombre
    with transaction.atomic():
        InventarioSucursal.objects.filter(sucursal=sucursal).delete()
        Categoria.objects.filter(sucursal=sucursal).delete()
        sucursal.delete()
    messages.success(request, f'"{nombre}" fue eliminada.')
    return redirect("panel:sucursales")


@login_required
@require_POST
def sucursal_inicializar(request, pk):
    """Inicializa una sucursal vacia copiando categorias + inventario de
    otra sucursal ya cargada.

    Arquitectura respetada (ver productos/models.py):
    - Producto es GLOBAL: nunca se duplica, el inventario nuevo apunta al
      mismo objeto Producto que ya existia.
    - Categoria pertenece a una sucursal (unique_together sucursal+nombre):
      se crean categorias NUEVAS para el destino (incluso si el nombre
      coincide con una de origen, son filas distintas), y cada inventario
      copiado apunta a la categoria nueva correspondiente -- nunca a la de
      origen.
    - El stock arranca en 0 y "disponible" en False: es una sucursal que
      recien esta empezando, sin stock real todavia cargado por un
      administrador (mismo criterio que producto_crear/InventarioForm, que
      no asume disponibilidad hasta que alguien la confirme).

    Si el destino ya tiene algun inventario, no se ejecuta nada -- se evita
    por completo el riesgo de duplicados en vez de pedir una confirmacion
    extra sobre datos ya reales.
    """
    _exigir_superusuario(request)
    destino = get_object_or_404(Sucursal, pk=pk)

    if InventarioSucursal.objects.filter(sucursal=destino).exists():
        messages.warning(request, f'"{destino.nombre}" ya tiene productos cargados. No se realizó ninguna modificación.')
        return redirect("panel:sucursales")

    form = SucursalInicializarForm(request.POST, destino=destino)
    if not form.is_valid():
        messages.error(request, "No se pudo inicializar la sucursal. No se realizaron cambios.")
        return redirect("panel:sucursales")

    origen = form.cleaned_data["origen"]
    try:
        with transaction.atomic():
            categorias_origen = list(Categoria.objects.filter(sucursal=origen))
            mapa_categorias = {}
            for categoria in categorias_origen:
                nueva_categoria, _ = Categoria.objects.get_or_create(
                    sucursal=destino,
                    nombre=categoria.nombre,
                    defaults={"descripcion": categoria.descripcion, "activo": categoria.activo},
                )
                mapa_categorias[categoria.id] = nueva_categoria

            inventarios_origen = list(
                InventarioSucursal.objects.filter(sucursal=origen).select_related("producto", "categoria")
            )
            InventarioSucursal.objects.bulk_create([
                InventarioSucursal(
                    producto=inv.producto,
                    sucursal=destino,
                    categoria=mapa_categorias[inv.categoria_id],
                    stock=0,
                    disponible=False,
                )
                for inv in inventarios_origen
            ])
    except Exception:
        messages.error(request, "No se pudo inicializar la sucursal. No se realizaron cambios.")
        return redirect("panel:sucursales")

    messages.success(
        request,
        f'Se inicializó "{destino.nombre}" correctamente. Se agregaron {len(inventarios_origen)} productos y {len(mapa_categorias)} categorías.',
    )
    return redirect("panel:sucursales")


def _lista_usuarios_con_forms(**kwargs_edicion):
    """Usuarios normales + `.edit_form`/`.password_form` adjuntados para los
    modales de usuarios.html. `kwargs_edicion` se reenvia tal cual a
    `_adjuntar_form_edicion` (pk_error/form_con_error del modal de EDITAR
    que este invalido, si corresponde)."""
    lista = User.objects.filter(is_superuser=False).prefetch_related("sucursales_autorizadas").order_by("username")
    _adjuntar_form_edicion(lista, UsuarioEditarForm, "user", **kwargs_edicion)
    _adjuntar_form_password(lista, "pwd")
    for usuario in lista:
        # Fragmentos para que "Cambiar contraseña" (dentro del modal de
        # editar) y "Cancelar" (dentro del modal de contraseña) naveguen
        # entre ambos modales sin salir nunca de la pagina de usuarios.
        usuario.password_href = f"#password-usuario-{usuario.pk}"
        usuario.editar_href = f"#editar-usuario-{usuario.pk}"
    return lista


@login_required
def usuarios_lista(request):
    _exigir_superusuario(request)
    lista = _lista_usuarios_con_forms()
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
    lista = _lista_usuarios_con_forms()
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
        # Invalido: se vuelve a la lista con el modal de ESTE usuario
        # forzado abierto y los errores visibles (en vez de una pagina aparte).
        lista = _lista_usuarios_con_forms(pk_error=usuario.pk, form_con_error=form)
        return render(request, "panel/usuarios.html", {"usuarios": lista, "form": UsuarioCrearForm()})
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
        # Invalido: se vuelve a la lista con el modal de CONTRASEÑA de este
        # usuario forzado abierto y los errores visibles.
        lista = _lista_usuarios_con_forms()
        for u in lista:
            if u.pk == usuario.pk:
                u.password_form = form
                u.password_modal_forzado_abierto = True
        return render(request, "panel/usuarios.html", {"usuarios": lista, "form": UsuarioCrearForm()})
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


@login_required
@require_POST
def usuario_eliminar(request, pk):
    """Elimina definitivamente un usuario normal. Solo superusuario, mismo
    permiso que el resto de la gestión de usuarios.

    `is_superuser=False` en el get_object_or_404 (igual que en
    usuario_editar/usuario_password/usuario_toggle_activo) ya impide por sí
    solo que esta vista pueda alcanzar a un superusuario -- y por lo tanto
    también impide que el superusuario que hace el pedido se elimine a sí
    mismo, dejando siempre al menos un administrador con acceso.
    """
    _exigir_superusuario(request)
    usuario = get_object_or_404(User, pk=pk, is_superuser=False)
    nombre = usuario.username
    try:
        usuario.delete()
    except ProtectedError:
        messages.error(
            request,
            f'No se pudo eliminar "{nombre}": todavía tiene datos relacionados. '
            "Desactivalo en vez de eliminarlo, o quitá esos datos e intentá de nuevo.",
        )
        return redirect("panel:usuarios")
    messages.success(request, f'"{nombre}" fue eliminado.')
    return redirect("panel:usuarios")
