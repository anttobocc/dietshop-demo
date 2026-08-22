from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from productos.models import Categoria, InventarioSucursal, Producto
from sucursales.models import Sucursal

User = get_user_model()


class ProductoGlobalForm(forms.ModelForm):
    """Datos del producto compartidos por toda la cadena (no por sucursal).

    El precio (y precio anterior) son datos globales pero, a diferencia del
    resto (nombre, descripcion, imagen, destacado/nuevo/oferta), cualquier
    usuario autorizado en una sucursal puede modificarlos -- no solo el
    superusuario. `solo_precio=True` recorta el formulario a esos dos
    campos, sin duplicar la definicion de Meta.fields/widgets.

    Producto.activo (estado global) no forma parte de este formulario: el
    panel ya no lo usa, la disponibilidad se maneja por sucursal via
    InventarioSucursal.disponible (ver InventarioForm). El campo se deja en
    el modelo para no romper datos historicos, simplemente no se expone
    aca.
    """

    class Meta:
        model = Producto
        fields = [
            "nombre",
            "precio",
            "precio_anterior",
            "descripcion",
            "imagen",
            "destacado",
            "nuevo",
            "oferta",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            # FileInput simple: sin el bloque "Actualmente: ... / Borrar" que
            # agrega Django por defecto (ClearableFileInput). Si no se elige
            # un archivo nuevo, Producto.imagen conserva el actual (Django lo
            # resuelve solo via FileField.clean, independiente del widget).
            "imagen": forms.FileInput(),
            # Switch visual sobre el mismo <input type="checkbox"> (ver
            # .switch-input en panel.css): no cambia lo que Django recibe.
            "destacado": forms.CheckboxInput(attrs={"class": "switch-input"}),
            "nuevo": forms.CheckboxInput(attrs={"class": "switch-input"}),
            "oferta": forms.CheckboxInput(attrs={"class": "switch-input"}),
        }

    CAMPOS_SOLO_PRECIO = ("precio", "precio_anterior")

    def __init__(self, *args, solo_precio=False, **kwargs):
        super().__init__(*args, **kwargs)
        if solo_precio:
            for nombre_campo in list(self.fields):
                if nombre_campo not in self.CAMPOS_SOLO_PRECIO:
                    del self.fields[nombre_campo]


class InventarioForm(forms.ModelForm):
    """Datos propios de UNA sucursal para un producto: categoría, stock, disponibilidad."""

    class Meta:
        model = InventarioSucursal
        fields = ["categoria", "stock", "disponible"]
        widgets = {
            "disponible": forms.CheckboxInput(attrs={"class": "switch-input"}),
        }

    def __init__(self, *args, sucursal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sucursal = sucursal
        if sucursal is not None:
            queryset = Categoria.objects.filter(sucursal=sucursal, activo=True)
            # Al editar, si la categoria ya asignada a este inventario se
            # desactivo despues (ver categoria_toggle_activo), igual se
            # incluye en las opciones aunque este inactiva: si no, el
            # <select> no la reconoce como valor valido y se muestra vacio
            # ("- Select an option -") en vez de preseleccionada.
            if self.instance.pk and self.instance.categoria_id:
                queryset = queryset | Categoria.objects.filter(pk=self.instance.categoria_id, sucursal=sucursal)
            self.fields["categoria"].queryset = queryset

    def clean_categoria(self):
        categoria = self.cleaned_data.get("categoria")
        if categoria and self.sucursal is not None and categoria.sucursal_id != self.sucursal.id:
            # Defensa en profundidad: aunque el <select> ya viene filtrado
            # por sucursal, esto bloquea un POST manipulado con un id de
            # categoría de otra sucursal.
            raise forms.ValidationError("La categoría debe pertenecer a la sucursal activa.")
        return categoria


class CategoriaForm(forms.ModelForm):
    """Categoria.activo no forma parte de este formulario: se activa/desactiva
    solamente desde el switch de la lista de categorias (ver
    `panel.views.categoria_toggle_activo`), nunca desde crear/editar. El
    campo queda con `default=True` en el modelo, asi que una categoria
    nueva queda activa automaticamente."""

    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
        }


class SucursalForm(forms.ModelForm):
    """CRUD de sucursales + a qué usuarios (no superusuarios) se les da acceso.

    `ocultar_activo=True` (usado al CREAR) saca "activo" del formulario:
    Sucursal.activo ya tiene `default=True` en el modelo, asi que una
    sucursal nueva queda activa automaticamente.
    """

    class Meta:
        model = Sucursal
        fields = ["nombre", "direccion", "activo", "usuarios"]
        widgets = {
            "usuarios": forms.CheckboxSelectMultiple,
            "activo": forms.CheckboxInput(attrs={"class": "switch-input"}),
        }

    def __init__(self, *args, ocultar_activo=False, **kwargs):
        super().__init__(*args, **kwargs)
        # Los superusuarios ya tienen acceso a todas las sucursales por
        # defecto (ver sucursales.permisos.sucursales_permitidas), así que
        # no tiene sentido ofrecerlos en esta lista de asignación manual.
        self.fields["usuarios"].queryset = User.objects.filter(is_superuser=False).order_by("username")
        self.fields["usuarios"].required = False
        if ocultar_activo:
            del self.fields["activo"]


class UsuarioCrearForm(UserCreationForm):
    """Crea un usuario normal (nunca superusuario) y le asigna sucursales.

    Hereda de UserCreationForm: la contraseña se valida y se guarda siempre
    con set_password() (nunca texto plano), sin ningún manejo manual.

    No incluye "email" (no se usa en este sistema) ni "is_active": un
    usuario nuevo siempre queda activo (User.is_active ya tiene
    `default=True` en el modelo, reforzado explicitamente en `save()`); el
    estado solo se cambia despues desde el switch de la lista de usuarios.
    """

    sucursales = forms.ModelMultipleChoiceField(
        queryset=Sucursal.objects.all().order_by("nombre"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Sucursales asignadas",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name"]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # Un usuario creado desde este formulario nunca es administrador
        # global, sin importar qué venga en el POST: is_superuser/is_staff
        # no son campos de este formulario, así que ni siquiera se leen.
        usuario.is_superuser = False
        usuario.is_staff = False
        usuario.is_active = True
        if commit:
            usuario.save()
            usuario.sucursales_autorizadas.set(self.cleaned_data["sucursales"])
        return usuario


class SucursalInicializarForm(forms.Form):
    """Elige de que sucursal copiar categorias/inventario para inicializar
    una sucursal nueva y vacia. El queryset de origen se restringe en la
    vista (excluye la propia sucursal destino), no aca, porque necesita
    conocer cual es el destino."""

    origen = forms.ModelChoiceField(
        queryset=Sucursal.objects.none(),
        label="Copiar desde",
        empty_label="Seleccioná una sucursal",
    )

    def __init__(self, *args, destino=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Sucursal.objects.order_by("nombre")
        if destino is not None:
            queryset = queryset.exclude(pk=destino.pk)
        self.fields["origen"].queryset = queryset


class UsuarioEditarForm(forms.ModelForm):
    """Edita un usuario normal existente. NUNCA incluye is_superuser ni password:
    ese campo simplemente no forma parte de este formulario, así que un POST
    manipulado con esos datos no tiene ningún efecto.

    Tampoco incluye "email" (no se usa en este sistema) ni "is_active": el
    estado del usuario se cambia solamente desde el switch de la lista de
    usuarios (ver `panel.views.usuario_toggle_activo`), nunca desde este
    formulario de edición.
    """

    sucursales = forms.ModelMultipleChoiceField(
        queryset=Sucursal.objects.all().order_by("nombre"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Sucursales asignadas",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["sucursales"].initial = self.instance.sucursales_autorizadas.all()

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            usuario.sucursales_autorizadas.set(self.cleaned_data["sucursales"])
        return usuario
