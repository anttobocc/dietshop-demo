from django import forms

from productos.models import Categoria, InventarioSucursal, Producto


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
