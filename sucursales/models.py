from django.conf import settings
from django.db import models


class Sucursal(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)
    usuarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="sucursales_autorizadas",
        blank=True,
        help_text="Usuarios autorizados a trabajar en esta sucursal (no aplica a superusuarios, que tienen acceso a todas).",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "sucursal"
        verbose_name_plural = "sucursales"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
