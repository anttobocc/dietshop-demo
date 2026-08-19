from django.db import migrations


def asignar_sucursal_central(apps, schema_editor):
    Sucursal = apps.get_model("sucursales", "Sucursal")
    Categoria = apps.get_model("productos", "Categoria")
    central = Sucursal.objects.get(nombre="Sucursal Central")
    Categoria.objects.filter(sucursal__isnull=True).update(sucursal=central)


def revertir_asignacion(apps, schema_editor):
    Categoria = apps.get_model("productos", "Categoria")
    Sucursal = apps.get_model("sucursales", "Sucursal")
    central = Sucursal.objects.get(nombre="Sucursal Central")
    Categoria.objects.filter(sucursal=central).update(sucursal=None)


class Migration(migrations.Migration):

    dependencies = [
        ("productos", "0002_categoria_sucursal_alter_categoria_nombre_and_more"),
        ("sucursales", "0002_crear_sucursal_central"),
    ]

    operations = [
        migrations.RunPython(asignar_sucursal_central, revertir_asignacion),
    ]
