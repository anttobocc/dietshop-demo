from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from productos.models import Categoria, InventarioSucursal, Producto
from sucursales.models import Sucursal

User = get_user_model()


class ProductoGlobalForm(forms.ModelForm):
    """Datos del producto compartidos por toda la cadena (no por sucursal)."""

    class Meta:
        model = Producto
        fields = [
            "nombre",
            "precio",
            "precio_anterior",
            "descripcion",
            "imagen",
            "activo",
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
        }


class InventarioForm(forms.ModelForm):
    """Datos propios de UNA sucursal para un producto: categoría, stock, disponibilidad."""

    class Meta:
        model = InventarioSucursal
        fields = ["categoria", "stock", "disponible"]

    def __init__(self, *args, sucursal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sucursal = sucursal
        if sucursal is not None:
            self.fields["categoria"].queryset = Categoria.objects.filter(sucursal=sucursal, activo=True)

    def clean_categoria(self):
        categoria = self.cleaned_data.get("categoria")
        if categoria and self.sucursal is not None and categoria.sucursal_id != self.sucursal.id:
            # Defensa en profundidad: aunque el <select> ya viene filtrado
            # por sucursal, esto bloquea un POST manipulado con un id de
            # categoría de otra sucursal.
            raise forms.ValidationError("La categoría debe pertenecer a la sucursal activa.")
        return categoria


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activo"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 2})}


class SucursalForm(forms.ModelForm):
    """CRUD de sucursales + a qué usuarios (no superusuarios) se les da acceso."""

    class Meta:
        model = Sucursal
        fields = ["nombre", "direccion", "activo", "usuarios"]
        widgets = {"usuarios": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Los superusuarios ya tienen acceso a todas las sucursales por
        # defecto (ver sucursales.permisos.sucursales_permitidas), así que
        # no tiene sentido ofrecerlos en esta lista de asignación manual.
        self.fields["usuarios"].queryset = User.objects.filter(is_superuser=False).order_by("username")
        self.fields["usuarios"].required = False


class UsuarioCrearForm(UserCreationForm):
    """Crea un usuario normal (nunca superusuario) y le asigna sucursales.

    Hereda de UserCreationForm: la contraseña se valida y se guarda siempre
    con set_password() (nunca texto plano), sin ningún manejo manual.
    """

    sucursales = forms.ModelMultipleChoiceField(
        queryset=Sucursal.objects.all().order_by("nombre"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Sucursales asignadas",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # Un usuario creado desde este formulario nunca es administrador
        # global, sin importar qué venga en el POST: is_superuser/is_staff
        # no son campos de este formulario, así que ni siquiera se leen.
        usuario.is_superuser = False
        usuario.is_staff = False
        if commit:
            usuario.save()
            usuario.sucursales_autorizadas.set(self.cleaned_data["sucursales"])
        return usuario


class UsuarioEditarForm(forms.ModelForm):
    """Edita un usuario normal existente. NUNCA incluye is_superuser ni password:
    ese campo simplemente no forma parte de este formulario, así que un POST
    manipulado con esos datos no tiene ningún efecto.
    """

    sucursales = forms.ModelMultipleChoiceField(
        queryset=Sucursal.objects.all().order_by("nombre"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Sucursales asignadas",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["sucursales"].initial = self.instance.sucursales_autorizadas.all()

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        if commit:
            usuario.sucursales_autorizadas.set(self.cleaned_data["sucursales"])
        return usuario
