from django.db import migrations


def crear_sucursal_central(apps, schema_editor):
    Sucursal = apps.get_model("sucursales", "Sucursal")
    Sucursal.objects.get_or_create(
        nombre="Sucursal Central",
        defaults={"direccion": "", "activo": True},
    )


def eliminar_sucursal_central(apps, schema_editor):
    Sucursal = apps.get_model("sucursales", "Sucursal")
    Sucursal.objects.filter(nombre="Sucursal Central").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sucursales", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_sucursal_central, eliminar_sucursal_central),
    ]
