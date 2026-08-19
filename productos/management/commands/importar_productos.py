"""
Importa a la base de datos Django las 7 categorías y los 28 productos
que originalmente estaban hardcodeados en script.js.

Arquitectura actual (post-sucursales): el producto es global (Producto) y
su categoría/stock/disponibilidad son propios de una sucursal
(InventarioSucursal). Este comando importa siempre a "Sucursal Central",
que es la sucursal donde vivían estos datos desde el origen del proyecto.

Es seguro ejecutarlo varias veces:
- Categoria y Producto usan update_or_create por (sucursal, nombre) / nombre,
  así que sus datos de catálogo (descripción, precio, imagen, tags, etc.) se
  vuelven a sincronizar con esta lista en cada corrida, sin duplicar filas.
- InventarioSucursal usa get_or_create: el stock y la disponibilidad
  SOLO se inicializan la primera vez. Si ya existe, no se pisan valores que
  un administrador haya cargado desde el panel (igual que el comportamiento
  original, que nunca reescribía el stock en corridas posteriores).
"""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from productos.models import Categoria, InventarioSucursal, Producto
from sucursales.models import Sucursal

# Igual a `categories` en script.js (solo se usan nombre y descripción,
# que son los campos que existen en el modelo Categoria).
CATEGORIAS = [
    {"nombre": "Cereales", "descripcion": "Granolas, avenas y mixes."},
    {"nombre": "Frutos secos", "descripcion": "Premium, frescos y seleccionados."},
    {"nombre": "Semillas", "descripcion": "Chia, lino, sesamo y mix fitness."},
    {"nombre": "Suplementos", "descripcion": "Proteinas, colageno y apoyo diario."},
    {"nombre": "Sin TACC", "descripcion": "Opciones aptas para todos los dias."},
    {"nombre": "Harinas", "descripcion": "Integrales, vegetales y sin gluten."},
    {"nombre": "Snacks saludables", "descripcion": "Barritas, chips y antojos mejores."},
]

# Igual a `products` en script.js. `imagen` es el nombre de archivo tal cual
# aparece en assets/ (sin el prefijo "assets/"). `tags` reproduce el array
# `tags` original; "offer" se agrega también cuando el producto tiene
# `oldPrice`, tal como hace badgeMarkup() en script.js. `categoria` indica
# a qué InventarioSucursal (en Sucursal Central) pertenece el producto.
PRODUCTOS = [
    {"nombre": "Avena arrollada integral", "imagen": "avena-arrollada-integral.jpg", "precio": "1850", "precio_anterior": None, "categoria": "Cereales", "descripcion": "Bolsa de 1 kg para desayunos y recetas.", "tags": ["best"]},
    {"nombre": "Granola con miel y almendras", "imagen": "Granola-con-miel-y-almendras.jpg", "precio": "3200", "precio_anterior": "3850", "categoria": "Cereales", "descripcion": "Crunch natural con frutos secos seleccionados.", "tags": ["offer", "best"]},
    {"nombre": "Copos de maiz sin azucar", "imagen": "copos-de-maiz-sin-azucar.jpg", "precio": "2100", "precio_anterior": None, "categoria": "Cereales", "descripcion": "Livianos para combinar con yogur o leche.", "tags": []},
    {"nombre": "Mix desayuno energetico", "imagen": "mix-frutosecos-energia.jpg", "precio": "2750", "precio_anterior": None, "categoria": "Cereales", "descripcion": "Avena, pasas, semillas y coco en escamas.", "tags": ["new"]},
    {"nombre": "Almendras naturales x 500 g", "imagen": "almendras-naturales.jpg", "precio": "6900", "precio_anterior": None, "categoria": "Frutos secos", "descripcion": "Enteras, frescas y sin sal agregada.", "tags": ["best"]},
    {"nombre": "Nueces mariposa x 250 g", "imagen": "Nueces-mariposa.jpg", "precio": "4200", "precio_anterior": None, "categoria": "Frutos secos", "descripcion": "Fuente de grasas saludables.", "tags": ["best"]},
    {"nombre": "Castanas de caju x 250 g", "imagen": "castañas-de-caju.jpg", "precio": "5100", "precio_anterior": "5900", "categoria": "Frutos secos", "descripcion": "Textura cremosa y sabor suave.", "tags": ["offer"]},
    {"nombre": "Mix premium de frutos secos", "imagen": "mix-premium-frutos-secos.jpg", "precio": "6200", "precio_anterior": None, "categoria": "Frutos secos", "descripcion": "Almendras, nueces, caju, mani y pasas.", "tags": ["best", "new"]},
    {"nombre": "Semillas de chia x 1 kg", "imagen": "SEMILLAS-DE-CHIA.jpg", "precio": "4300", "precio_anterior": None, "categoria": "Semillas", "descripcion": "Fibra, omega 3 y textura versatil.", "tags": ["best"]},
    {"nombre": "Semillas de lino dorado", "imagen": "semillas-de-lino-doradas.jpg", "precio": "2600", "precio_anterior": None, "categoria": "Semillas", "descripcion": "Para moler, panes o licuados.", "tags": []},
    {"nombre": "Sesamo integral x 500 g", "imagen": "semilla-sesamo-integral.jpg", "precio": "2950", "precio_anterior": "3400", "categoria": "Semillas", "descripcion": "Sabor tostado para ensaladas y panes.", "tags": ["offer"]},
    {"nombre": "Mix de semillas fitness", "imagen": "mix-semillas.jpg", "precio": "3400", "precio_anterior": None, "categoria": "Semillas", "descripcion": "Chia, lino, girasol y sesamo.", "tags": ["new"]},
    {"nombre": "Proteina whey vainilla", "imagen": "proteina-whey.jpg", "precio": "16800", "precio_anterior": None, "categoria": "Suplementos", "descripcion": "Presentacion 900 g para entrenamiento.", "tags": ["best"]},
    {"nombre": "Colageno hidrolizado", "imagen": "colageno-hidrolizado.jpg", "precio": "7840", "precio_anterior": "9800", "categoria": "Suplementos", "descripcion": "Polvo neutro para bebidas frias o calientes.", "tags": ["offer", "best"]},
    {"nombre": "Magnesio citrato", "imagen": "magnesio-polvo.jpg", "precio": "7600", "precio_anterior": None, "categoria": "Suplementos", "descripcion": "Suplemento diario en capsulas.", "tags": ["new"]},
    {"nombre": "Levadura nutricional", "imagen": "levadura-nutricional.jpg", "precio": "5100", "precio_anterior": None, "categoria": "Suplementos", "descripcion": "Sabor tipo queso para platos vegetales.", "tags": []},
    {"nombre": "Premezcla sin TACC", "imagen": "premezcla-SinTacc.jpg", "precio": "3600", "precio_anterior": None, "categoria": "Sin TACC", "descripcion": "Para panificados y recetas caseras.", "tags": ["best"]},
    {"nombre": "Galletitas de arroz integral", "imagen": "galletitas-de-arroz.jpg", "precio": "1800", "precio_anterior": "2200", "categoria": "Sin TACC", "descripcion": "Livianas y practicas para colaciones.", "tags": ["offer"]},
    {"nombre": "Fideos de arroz", "imagen": "fideo-de-arroz.jpg", "precio": "2600", "precio_anterior": None, "categoria": "Sin TACC", "descripcion": "Rapidos para comidas livianas.", "tags": []},
    {"nombre": "Cookies sin TACC con chips", "imagen": "Cookies-sinTACC-con-chips.jpg", "precio": "2400", "precio_anterior": None, "categoria": "Sin TACC", "descripcion": "Dulces, suaves y listas para disfrutar.", "tags": ["new"]},
    {"nombre": "Harina integral fina", "imagen": "harina-integral.jpg", "precio": "2200", "precio_anterior": None, "categoria": "Harinas", "descripcion": "Para panes, pizzas y tartas.", "tags": []},
    {"nombre": "Harina de almendras", "imagen": "harina-de-almendra.jpg", "precio": "7900", "precio_anterior": "8900", "categoria": "Harinas", "descripcion": "Ideal para pasteleria saludable.", "tags": ["offer", "best"]},
    {"nombre": "Harina de garbanzos", "imagen": "harina-de-garbanzos.jpg", "precio": "3100", "precio_anterior": None, "categoria": "Harinas", "descripcion": "Proteica y sabrosa.", "tags": ["new"]},
    {"nombre": "Harina de arroz integral", "imagen": "harina-de-arroz.jpg", "precio": "2850", "precio_anterior": None, "categoria": "Harinas", "descripcion": "Textura suave para recetas sin gluten.", "tags": []},
    {"nombre": "Barrita de cereal y cacao", "imagen": "Barrita-de-cereal-y-cacao.jpg", "precio": "950", "precio_anterior": None, "categoria": "Snacks saludables", "descripcion": "Snack practico para llevar.", "tags": ["best"]},
    {"nombre": "Chips de banana deshidratada", "imagen": "Chips-de-banana.jpg", "precio": "2100", "precio_anterior": "2500", "categoria": "Snacks saludables", "descripcion": "Dulzor natural y textura crocante.", "tags": ["offer"]},
    {"nombre": "Garbanzos crocantes saborizados", "imagen": "Garbanzos-crocantes-saborizados.jpg", "precio": "2600", "precio_anterior": None, "categoria": "Snacks saludables", "descripcion": "Alternativa salada con proteina vegetal.", "tags": ["new"]},
    # script.js referencia "assets/Chocolate-amargo-70.jpg", pero el archivo real
    # en assets/ se llama "Chocolate-amargo-70%.jpg" (con %). Es una imagen rota
    # ya en el proyecto original: se deja sin copiar y se informa, tal como pide el paso 3.
    {"nombre": "Chocolate amargo 70%", "imagen": "Chocolate-amargo-70.jpg", "precio": "3300", "precio_anterior": None, "categoria": "Snacks saludables", "descripcion": "Tableta intensa con alto porcentaje de cacao.", "tags": ["best"]},
]


class Command(BaseCommand):
    help = "Importa las categorías y productos de script.js a Producto + InventarioSucursal (Sucursal Central)."

    def handle(self, *args, **options):
        central, _ = Sucursal.objects.get_or_create(nombre="Sucursal Central", defaults={"activo": True})

        assets_dir = Path(settings.BASE_DIR) / "assets"
        media_productos_dir = Path(settings.MEDIA_ROOT) / "productos"
        media_productos_dir.mkdir(parents=True, exist_ok=True)

        categorias_creadas = 0
        categorias_por_nombre = {}
        for data in CATEGORIAS:
            categoria, created = Categoria.objects.update_or_create(
                sucursal=central,
                nombre=data["nombre"],
                defaults={"descripcion": data["descripcion"], "activo": True},
            )
            categorias_por_nombre[data["nombre"]] = categoria
            categorias_creadas += created

        productos_creados = 0
        inventarios_creados = 0
        imagenes_copiadas = 0
        imagenes_faltantes = []

        for data in PRODUCTOS:
            categoria = categorias_por_nombre[data["categoria"]]

            imagen_rel = None
            origen = assets_dir / data["imagen"]
            if origen.exists():
                destino = media_productos_dir / data["imagen"]
                shutil.copyfile(origen, destino)
                imagenes_copiadas += 1
                imagen_rel = f"productos/{data['imagen']}"
            else:
                imagenes_faltantes.append((data["nombre"], f"assets/{data['imagen']}"))

            tags = list(data["tags"])
            if data["precio_anterior"] and "offer" not in tags:
                tags.append("offer")

            # Datos GLOBALES del producto (comparten todas las sucursales).
            producto_defaults = {
                "precio": data["precio"],
                "precio_anterior": data["precio_anterior"],
                "descripcion": data["descripcion"],
                "tags": ",".join(tags),
                "destacado": "best" in tags,
                "nuevo": "new" in tags,
                "oferta": "offer" in tags,
                "activo": True,
            }
            if imagen_rel:
                producto_defaults["imagen"] = imagen_rel

            producto, created = Producto.objects.update_or_create(
                nombre=data["nombre"],
                defaults=producto_defaults,
            )
            productos_creados += created

            # Inventario en Sucursal Central: stock y disponibilidad son datos
            # operativos. Solo se inicializan al crear; si ya existe la fila
            # (por ejemplo porque un administrador cargó stock desde el panel),
            # NO se pisan en corridas posteriores del comando.
            _, inv_created = InventarioSucursal.objects.get_or_create(
                producto=producto,
                sucursal=central,
                defaults={"categoria": categoria, "stock": 0, "disponible": True},
            )
            inventarios_creados += inv_created

        self.stdout.write(self.style.SUCCESS(
            f"Categorías: {Categoria.objects.filter(sucursal=central).count()} en Sucursal Central "
            f"({categorias_creadas} nuevas/actualizadas en esta corrida)."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Productos: {Producto.objects.count()} en base "
            f"({productos_creados} nuevos en esta corrida)."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"InventarioSucursal en Central: {InventarioSucursal.objects.filter(sucursal=central).count()} "
            f"({inventarios_creados} nuevos en esta corrida)."
        ))
        self.stdout.write(f"Imágenes copiadas a media/productos/: {imagenes_copiadas}")

        if imagenes_faltantes:
            self.stdout.write(self.style.WARNING("Imágenes faltantes (no se copiaron ni se inventaron):"))
            for nombre, ruta in imagenes_faltantes:
                self.stdout.write(self.style.WARNING(f"  - {nombre}: {ruta} no existe en assets/"))
