from django.db import migrations


def crear_inventario_central(apps, schema_editor):
    Sucursal = apps.get_model("sucursales", "Sucursal")
    Producto = apps.get_model("productos", "Producto")
    InventarioSucursal = apps.get_model("productos", "InventarioSucursal")

    central = Sucursal.objects.get(nombre="Sucursal Central")

    for producto in Producto.objects.all():
        InventarioSucursal.objects.get_or_create(
            producto=producto,
            sucursal=central,
            defaults={
                "categoria_id": producto.categoria_id,
                "stock": producto.stock,
                "disponible": producto.activo,
            },
        )


def eliminar_inventario_central(apps, schema_editor):
    Sucursal = apps.get_model("sucursales", "Sucursal")
    InventarioSucursal = apps.get_model("productos", "InventarioSucursal")
    central = Sucursal.objects.get(nombre="Sucursal Central")
    InventarioSucursal.objects.filter(sucursal=central).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0004_inventariosucursal"),
        ("sucursales", "0002_crear_sucursal_central"),
    ]

    operations = [
        migrations.RunPython(crear_inventario_central, eliminar_inventario_central),
    ]
