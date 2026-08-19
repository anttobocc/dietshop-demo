from django import forms

from productos.models import Categoria, Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre",
            "categoria",
            "precio",
            "precio_anterior",
            "descripcion",
            "imagen",
            "stock",
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


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activo"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 2})}
