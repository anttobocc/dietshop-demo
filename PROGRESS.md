# PROGRESS — Grandiet Demo

Archivo de seguimiento de tareas. Actualizar a medida que se completen.

---

## Completado ✅

- [x] Exploración inicial del proyecto y análisis de código
- [x] Creación del PRD con objetivos y prioridades
- [x] Creación de este archivo de progreso
- [x] Cambio de número WhatsApp a +54 9 379 475-7727 en script.js, index.html y catalogo.html
- [x] Firebase Auth y Firestore habilitados en consola Firebase
- [x] Actualizar firebase.js con Auth + operaciones de escritura (addDoc, updateDoc, deleteDoc)
- [x] Conectar script.js a Firestore — productos se cargan dinámicamente (eliminado array hardcodeado)
- [x] Validación del nombre del cliente antes de enviar pedido por WhatsApp
- [x] Crear admin.html — panel con login, tabla de productos, modal de creación/edición/borrado
- [x] Agregar type="module" a script tags en index.html y catalogo.html

---

## En progreso 🔄

_(ninguna tarea en curso)_

---

## Pendiente 📋

### Crítico (Must Have)
- [ ] Verificar que `index.html` y `catalogo.html` cargan productos correctamente desde Firestore
- [ ] Verificar login y CRUD en `admin.html`
- [ ] Completar datos de productos en Firestore (imágenes, tags, oldPrice) usando el panel admin

### Importante (Should Have)
- [ ] Modal o página de detalle de producto
- [ ] Indicador de stock por producto
- [ ] Campo de notas/comentarios en el carrito
- [ ] Convertir imágenes a formato WebP para mejor performance
- [ ] Agregar README.md con instrucciones de setup y despliegue

### Deseable (Could Have)
- [ ] Ordenamiento del catálogo (precio, popularidad, novedad)
- [ ] Firebase Analytics para rastrear pedidos y búsquedas
- [ ] Service Worker para funcionalidad básica offline (PWA)
- [ ] Meta tags SEO y Open Graph para compartir en redes

---

## Notas y Decisiones

| Fecha      | Nota |
|------------|------|
| 2026-06-02 | Análisis inicial completado. Stack: HTML + CSS + Vanilla JS + Firebase sin integrar. 28 productos hardcodeados. |
| 2026-06-02 | PRD creado. Prioridad máxima: Firestore + admin panel + modularización. |
| 2026-06-02 | Firebase completamente integrado. Productos ahora vienen de Firestore. admin.html operativo. |
