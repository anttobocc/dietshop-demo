from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    # Nullable temporalmente durante la migración incremental a sucursales;
    # se vuelve obligatorio (null=False) en una etapa posterior, una vez
    # que las 7 categorías existentes ya tengan sucursal asignada.
    sucursal = models.ForeignKey(
        "sucursales.Sucursal",
        on_delete=models.PROTECT,
        related_name="categorias",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(fields=["sucursal", "nombre"], name="categoria_unica_por_sucursal"),
        ]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to="productos/", null=True, blank=True)
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    nuevo = models.BooleanField(default=False)
    oferta = models.BooleanField(default=False)
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text="Lista separada por comas, ej: best,new,offer",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class InventarioSucursal(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="inventarios",
    )
    sucursal = models.ForeignKey(
        "sucursales.Sucursal",
        on_delete=models.PROTECT,
        related_name="inventarios",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="inventarios",
    )
    stock = models.PositiveIntegerField(default=0)
    disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "inventario por sucursal"
        verbose_name_plural = "inventarios por sucursal"
        constraints = [
            models.UniqueConstraint(fields=["producto", "sucursal"], name="inventario_unico_por_sucursal"),
        ]

    def __str__(self):
        return f"{self.producto} - {self.sucursal}"
