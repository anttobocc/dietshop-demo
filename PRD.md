# PRD — Grandiet Corrientes: Tienda Online de Alimentos Saludables

## Resumen del Producto

Grandiet Corrientes es una tienda online de alimentos saludables ubicada en Corrientes, Argentina. El sitio permite a los clientes explorar el catálogo de productos, filtrarlos por categoría, agregarlos al carrito y hacer el pedido directamente por WhatsApp. El foco es velocidad, simplicidad y conversión directa sin necesidad de gateway de pagos.

**Stack actual:** HTML5 + CSS3 + Vanilla JavaScript (ES6+) + Django (backend, ORM, panel de administración) + SQLite + localStorage para carrito.

> **Actualización:** el proyecto usó Firebase (Auth + Firestore) durante una etapa anterior. Fue reemplazado completamente por Django: el catálogo público consume `/api/productos/` y `/api/categorias/` (Django ORM + SQLite), y la administración se hace desde el panel propio en `/panel/` (Django Authentication + CRUD). Firebase ya no forma parte del código del proyecto.

---

## Estado Actual

- 28 productos en 7 categorías (modelo `Producto`/`Categoria` de Django, servidos vía `/api/productos/` y `/api/categorias/`)
- Carrito funcional con persistencia en localStorage
- Integración con WhatsApp para hacer pedidos
- Carousel de promociones en la home
- Filtros por categoría, tag y búsqueda en el catálogo
- Panel de administración propio en `/panel/` (login con Django Authentication, dashboard, CRUD de productos y categorías, activar/desactivar productos)
- Sin validación de formularios
- Sin documentación

---

## Objetivos de Mejora

### 1. Integridad del Código
- Eliminar o integrar correctamente Firebase
- Separar la lógica en módulos (cart.js, products.js, ui.js)
- Agregar validación en el formulario del carrito (nombre del cliente)
- Limpiar magic numbers (número de WhatsApp, timer del carousel)

### 2. Gestión de Contenido (sin código)
- **Panel de administración** para que el dueño del negocio pueda: ✅ implementado en `/panel/`
  - Agregar / editar / eliminar productos
  - Cambiar precios y ofertas
  - Gestionar imágenes
- Backend: Django ORM + SQLite como base de datos de productos
- Autenticación con Django Authentication para el panel admin

### 3. Experiencia del Usuario (UX)
- Página de detalle de producto (modal o página dedicada)
- Mejora del flujo del carrito: confirmación antes de enviar por WhatsApp
- Campo de notas/comentarios en el pedido
- Indicador de stock ("últimas unidades", "sin stock")
- Ordenamiento del catálogo (por precio, popularidad, novedad)

### 4. Performance y Técnico
- Convertir imágenes a WebP
- Agregar un archivo de configuración del negocio (config.js o Firestore)
- Service Worker para funcionalidad offline básica
- Meta tags de SEO y Open Graph para redes sociales

### 5. Analítica y Seguimiento
- Integrar Google Analytics o Firebase Analytics
- Rastrear: vistas de producto, búsquedas, pedidos enviados

---

## Prioridades (MoSCoW)

### Must Have (crítico)
- [x] Integrar productos con Django ORM/SQLite (eliminar hardcode) — completado, reemplaza el plan original de Firestore
- [x] Panel de administración básico (CRUD de productos) — completado en `/panel/` con Django
- [ ] Validación del nombre del cliente antes de enviar pedido
- [ ] Archivo de configuración del negocio (teléfono, horarios)
- [ ] Modularizar el JavaScript

### Should Have (importante)
- [ ] Página/modal de detalle de producto
- [ ] Indicador de stock
- [ ] Optimización de imágenes (WebP)
- [ ] Campo de notas en el pedido

### Could Have (deseable)
- [ ] Ordenamiento del catálogo
- [ ] Service Worker / PWA
- [ ] Analítica básica (Firebase Analytics)

### Won't Have (por ahora)
- Pasarela de pagos (Mercado Pago, etc.)
- Sistema de usuarios/cuentas para clientes
- Reviews/opiniones de productos

---

## Métricas de Éxito

- Pedidos por WhatsApp generados por el sitio (trackear con parámetros UTM)
- Tiempo en página > 2 minutos
- Tasa de rebote < 60%
- El dueño puede actualizar precios/productos sin tocar código

---

## Notas Técnicas

- El número de WhatsApp hardcodeado es `+54 9 379 400-0000` — debe moverse a config
- Firebase (Auth + Firestore) fue usado en una etapa anterior del proyecto y ya fue eliminado del repositorio (`firebase.js` y `admin.html` no existen más). El catálogo público y el panel de administración funcionan exclusivamente con Django.
- No hay proceso de build — considerar Vite o simplemente módulos ES nativos
