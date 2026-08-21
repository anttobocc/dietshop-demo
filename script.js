const WHATSAPP_NUMBER = "5493794000000";
const CART_KEY = "grandiet-cart";
const SUCURSAL_KEY = "sucursalSeleccionada";

// Estilo visual (color/icono) de cada categoria para las tarjetas de la home.
// Es solo presentacion: los datos reales de categorias y productos vienen de Django (/api/).
const CATEGORY_STYLES = {
  "Cereales": { color: "#dff0c2", icon: "grain" },
  "Frutos secos": { color: "#f8e0c7", icon: "nut" },
  "Semillas": { color: "#e8f3d5", icon: "seed" },
  "Suplementos": { color: "#dceef7", icon: "plus" },
  "Sin TACC": { color: "#f7ebbd", icon: "check" },
  "Harinas": { color: "#efe4cf", icon: "bag" },
  "Snacks saludables": { color: "#fbd8c6", icon: "spark" },
};
const DEFAULT_CATEGORY_STYLE = { color: "#eef1e6", icon: "bag" };

const productImage = "assets/product-pattern.svg";

// Se completan con fetch("/api/categorias/") y fetch("/api/productos/") antes de renderizar.
let categories = [];
let products = [];

// Sucursal pública seleccionada por el visitante (independiente de login/panel).
let sucursales = [];
let sucursalActual = null;

const slides = [
  { title: "Colageno hidrolizado", kicker: "20% OFF", description: "Promo destacada por tiempo limitado. Sumalo a tu pedido y confirma stock por WhatsApp.", category: "Suplementos", image: "assets/colageno-hidrolizado.jpg", bg: "#eef6e3", discount: "20%" },
  { title: "Frutos secos premium", kicker: "Seleccion especial", description: "Mixes frescos para desayunos, meriendas y picadas saludables.", category: "Frutos secos", image: "assets/mix-premium-frutos-secos.jpg", bg: "#fff3e7" },
  { title: "Productos Sin TACC", kicker: "Aptos y practicos", description: "Premezclas, snacks y opciones para resolver tus compras rapido.", category: "Sin TACC", image: "assets/productos-sin-TACC.jpg", bg: "#fff8db" },
  { title: "Envios a domicilio", kicker: "Compra comoda", description: "Arma el carrito, envia el pedido y coordinamos entrega o retiro.", category: "Todos", image: "assets/envios.jpg", bg: "#e7f4d5" },
  { title: "Suplementos deportivos", kicker: "Nueva seleccion", description: "Proteinas y complementos para entrenar con mejor organizacion.", category: "Suplementos", image: "assets/suplementos-deportivos.jpg", bg: "#e8f4f7" },
];

let activeCategory = "Todos";
let activeTag = "Todos";
let searchTerm = "";
let currentSlide = 0;
let slideTimer;
const cart = new Map(JSON.parse(localStorage.getItem(CART_KEY) || "[]"));

const els = {
  menuToggle: document.querySelector(".menu-toggle"),
  navLinks: document.querySelector("#primary-menu"),
  openCart: document.querySelector("#openCart"),
  cartDrawer: document.querySelector("#cartDrawer"),
  cartItems: document.querySelector("#cartItems"),
  cartEmpty: document.querySelector("#cartEmpty"),
  cartCount: document.querySelector("#cartCount"),
  subtotal: document.querySelector("#subtotal"),
  sendOrder: document.querySelector("#sendOrder"),
  customerName: document.querySelector("#customerName"),
  categoryCards: document.querySelector("#categoryCards"),
  productGrid: document.querySelector("#productGrid"),
  resultCount: document.querySelector("#resultCount"),
  clearFilters: document.querySelector("#clearFilters"),
  searchInput: document.querySelector("#searchInput"),
  filterButtons: document.querySelector("#filterButtons"),
  tagButtons: document.querySelector("#tagButtons"),
  carouselTrack: document.querySelector("#carouselTrack"),
  carouselDots: document.querySelector("#carouselDots"),
  prevSlide: document.querySelector("#prevSlide"),
  nextSlide: document.querySelector("#nextSlide"),
  bestSellerGrid: document.querySelector("#bestSellerGrid"),
  offerGrid: document.querySelector("#offerGrid"),
  sucursalTrigger: document.querySelector("#sucursalTrigger"),
  sucursalActualLabel: document.querySelector("#sucursalActualLabel"),
  sucursalTriggerCaret: document.querySelector(".sucursal-trigger-caret"),
  sucursalModal: document.querySelector("#sucursalModal"),
  sucursalModalClose: document.querySelector("#sucursalModalClose"),
  sucursalList: document.querySelector("#sucursalList"),
};

function money(value) {
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(value);
}

function productImageFor(product) {
  return product.image || productImage;
}

// El carrito persiste en localStorage y puede contener una "foto" vieja del
// producto (guardada en el momento en que se agrego al carrito). Si ese
// producto sigue estando en el catalogo actual, usamos su imagen VIGENTE
// (la misma fuente que usa el catalogo) en vez de la version cacheada, que
// puede apuntar a una ruta que ya no existe.
function cartItemImageSrc(cartProduct) {
  const vigente = products.find((item) => item.id === cartProduct.id);
  return productImageFor(vigente || cartProduct);
}

function badgeMarkup(product) {
  const badges = [];
  if (product.oldPrice) badges.push(`<span class="badge offer">${Math.round((1 - product.price / product.oldPrice) * 100)}% OFF</span>`);
  if (product.tags.includes("new")) badges.push(`<span class="badge new">Nuevo</span>`);
  if (product.tags.includes("best")) badges.push(`<span class="badge">Mas vendido</span>`);
  return badges.length ? `<div class="badges">${badges.join("")}</div>` : "";
}

function icon(name) {
  const paths = {
    grain: "M4 4c7 0 13 6 13 13h-2C15 11.1 9.9 6 4 6V4Zm0 5c4.4 0 8 3.6 8 8h-2c0-3.3-2.7-6-6-6V9Zm0 5c1.7 0 3 1.3 3 3H4v-3Z",
    nut: "M12 3c4 0 7 3.6 7 8.2 0 5.4-3.1 9.8-7 9.8s-7-4.4-7-9.8C5 6.6 8 3 12 3Zm0 2C9.2 5 7 7.7 7 11.2 7 15.5 9.3 19 12 19s5-3.5 5-7.8C17 7.7 14.8 5 12 5Z",
    seed: "M20.5 3.5C13 3.7 6.4 8 5.3 15.4L3 18l1.4 1.4 2.2-2.2C13.9 16.1 18.2 10 20.5 3.5ZM7.5 14.4c1.2-4 4.5-7 9.2-8.2-2 4.3-5 7.2-9.2 8.2Z",
    plus: "M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5Z",
    check: "m10 15.2 7.1-7.1 1.4 1.4L10 18 5.5 13.5l1.4-1.4 3.1 3.1Z",
    bag: "M7 7V6a5 5 0 0 1 10 0v1h2v14H5V7h2Zm2 0h6V6a3 3 0 0 0-6 0v1Zm-2 2v10h10V9H7Z",
    spark: "m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z",
  };
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name]}"/></svg>`;
}

function saveCart() {
  localStorage.setItem(CART_KEY, JSON.stringify([...cart.entries()]));
}

function renderCategories() {
  if (!els.categoryCards) return;
  els.categoryCards.innerHTML = categories.map((category) => {
    const style = CATEGORY_STYLES[category.name] || DEFAULT_CATEGORY_STYLE;
    return `
    <a class="category-card" href="catalogo.html?category=${encodeURIComponent(category.name)}" style="--category-color:${style.color}">
      <span>${icon(style.icon)}</span>
      <h3>${category.name}</h3>
      <p>${category.description}</p>
    </a>
  `;
  }).join("");
}

function renderFilterButtons() {
  if (els.filterButtons) {
    const filters = ["Todos", ...categories.map((category) => category.name)];
    els.filterButtons.innerHTML = filters.map((filter) => `
      <button class="filter-btn ${filter === activeCategory ? "is-active" : ""}" type="button" data-category="${filter}" role="listitem">${filter}</button>
    `).join("");
  }

  if (els.tagButtons) {
    const tags = [
      { label: "Todos", value: "Todos" },
      { label: "Ofertas", value: "offer" },
      { label: "Mas vendidos", value: "best" },
      { label: "Nuevos", value: "new" },
    ];
    els.tagButtons.innerHTML = tags.map((tag) => `
      <button class="filter-btn ${tag.value === activeTag ? "is-active" : ""}" type="button" data-tag="${tag.value}" role="listitem">${tag.label}</button>
    `).join("");
  }
}

function filteredProducts() {
  return products.filter((product) => {
    const matchesCategory = activeCategory === "Todos" || product.category === activeCategory;
    const matchesTag = activeTag === "Todos" || product.tags.includes(activeTag) || (activeTag === "offer" && product.oldPrice);
    const term = searchTerm.trim().toLowerCase();
    const matchesSearch = !term || `${product.name} ${product.category} ${product.description}`.toLowerCase().includes(term);
    return matchesCategory && matchesTag && matchesSearch;
  });
}

function renderProductCard(product) {
  return `
    <article class="product-card">
      ${badgeMarkup(product)}
      <img src="${productImageFor(product)}" alt="${product.name}" loading="lazy">
      <div class="product-body">
        <div class="product-meta">
          <span class="tag">${product.category}</span>
          <span class="price-wrap">
            ${product.oldPrice ? `<span class="old-price">${money(product.oldPrice)}</span>` : ""}
            <strong class="price">${money(product.price)}</strong>
          </span>
        </div>
        <h3>${product.name}</h3>
        <p>${product.description}</p>
        <button class="add-btn" type="button" data-add="${product.id}">Agregar al carrito</button>
      </div>
    </article>
  `;
}

function renderProducts() {
  if (!els.productGrid) return;
  const visibleProducts = filteredProducts();
  if (els.resultCount) els.resultCount.textContent = `${visibleProducts.length} producto${visibleProducts.length === 1 ? "" : "s"}`;
  els.productGrid.innerHTML = visibleProducts.length
    ? visibleProducts.map(renderProductCard).join("")
    : `<p class="product-card product-body">No encontramos productos con ese criterio.</p>`;
}

function renderHomeProducts() {
  if (els.bestSellerGrid) {
    els.bestSellerGrid.innerHTML = products.filter((product) => product.tags.includes("best")).slice(0, 4).map(renderProductCard).join("");
  }
  if (els.offerGrid) {
    els.offerGrid.innerHTML = products.filter((product) => product.oldPrice).slice(0, 4).map(renderProductCard).join("");
  }
}

function renderCarousel() {
  if (!els.carouselTrack || !els.carouselDots) return;
  els.carouselTrack.innerHTML = slides.map((slide) => `
    <article class="promo-slide" style="--slide-bg:${slide.bg}">
      <div class="promo-copy">
        <span class="promo-kicker">${slide.kicker}</span>
        <h2>${slide.title}</h2>
        <p>${slide.description}</p>
        <a class="btn btn-primary" href="catalogo.html?category=${encodeURIComponent(slide.category)}">Comprar ahora</a>
      </div>
      <div class="promo-art">
        <img src="${slide.image}" alt="${slide.title}">
        ${slide.discount ? `<span class="promo-discount">${slide.discount}</span>` : ""}
      </div>
    </article>
  `).join("");
  els.carouselDots.innerHTML = slides.map((_, index) => `
    <button type="button" class="${index === currentSlide ? "is-active" : ""}" data-slide="${index}" aria-label="Ver promocion ${index + 1}"></button>
  `).join("");
  updateCarousel();
  slideTimer = setInterval(() => goToSlide(currentSlide + 1), 5200);
}

function updateCarousel() {
  if (!els.carouselTrack || !els.carouselDots) return;
  els.carouselTrack.style.transform = `translateX(-${currentSlide * 100}%)`;
  els.carouselDots.querySelectorAll("button").forEach((button, index) => {
    button.classList.toggle("is-active", index === currentSlide);
  });
}

function goToSlide(index) {
  currentSlide = (index + slides.length) % slides.length;
  updateCarousel();
}

function resetSlideTimer() {
  if (!slideTimer) return;
  clearInterval(slideTimer);
  slideTimer = setInterval(() => goToSlide(currentSlide + 1), 5200);
}

function cartTotals() {
  return [...cart.values()].reduce((acc, item) => {
    acc.quantity += item.quantity;
    acc.subtotal += item.quantity * item.product.price;
    return acc;
  }, { quantity: 0, subtotal: 0 });
}

function renderCart() {
  const items = [...cart.values()];
  const totals = cartTotals();
  if (els.cartItems) {
    els.cartItems.innerHTML = items.map(({ product, quantity }) => `
      <div class="cart-item">
        <img class="cart-thumb" src="${cartItemImageSrc(product)}" alt="${product.name}" loading="lazy">
        <div class="cart-item-info">
          <strong>${product.name}</strong>
          <small>${money(product.price)}</small>
          <div class="quantity" aria-label="Cantidad de ${product.name}">
            <button type="button" data-decrease="${product.id}" aria-label="Restar ${product.name}">-</button>
            <strong>${quantity}</strong>
            <button type="button" data-increase="${product.id}" aria-label="Sumar ${product.name}">+</button>
            <button class="remove-item" type="button" data-remove="${product.id}" aria-label="Eliminar ${product.name}">Eliminar</button>
          </div>
        </div>
      </div>
    `).join("");
  }
  if (els.cartEmpty) els.cartEmpty.hidden = items.length > 0;
  if (els.cartCount) els.cartCount.textContent = totals.quantity;
  if (els.subtotal) els.subtotal.textContent = money(totals.subtotal);
  if (els.sendOrder) els.sendOrder.disabled = items.length === 0;
  saveCart();
}

function openCart() {
  if (!els.cartDrawer) return;
  els.cartDrawer.classList.add("is-open");
  els.cartDrawer.setAttribute("aria-hidden", "false");
  els.openCart?.setAttribute("aria-expanded", "true");
  document.body.classList.add("cart-open");
}

function closeCart() {
  if (!els.cartDrawer) return;
  els.cartDrawer.classList.remove("is-open");
  els.cartDrawer.setAttribute("aria-hidden", "true");
  els.openCart?.setAttribute("aria-expanded", "false");
  document.body.classList.remove("cart-open");
}

function addToCart(id) {
  const product = products.find((item) => item.id === Number(id));
  if (!product) return;
  const current = cart.get(String(product.id));
  cart.set(String(product.id), { product, quantity: current ? current.quantity + 1 : 1 });
  renderCart();
  openCart();
}

function updateQuantity(id, delta) {
  const key = String(id);
  const item = cart.get(key);
  if (!item) return;
  const nextQuantity = item.quantity + delta;
  if (nextQuantity <= 0) cart.delete(key);
  else cart.set(key, { ...item, quantity: nextQuantity });
  renderCart();
}

function removeFromCart(id) {
  cart.delete(String(id));
  renderCart();
}

function sendOrder() {
  if (!cart.size) return;
  const totals = cartTotals();
  const name = els.customerName?.value.trim() || "";
  const lines = [...cart.values()].map(({ product, quantity }) => `* ${product.name} x ${quantity}`);
  const message = [
    "Hola Grandiet Corrientes.",
    "",
    "Quisiera realizar el siguiente pedido:",
    "",
    ...lines,
    "",
    `Total estimado: ${money(totals.subtotal)}`,
    "",
    `Mi nombre es: ${name}`,
  ].join("\n");
  window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`, "_blank", "noopener");
}

function applyUrlFilters() {
  const params = new URLSearchParams(window.location.search);
  const category = params.get("category");
  const query = params.get("q");
  const tag = params.get("tag");
  if (category && (category === "Todos" || categories.some((item) => item.name === category))) activeCategory = category;
  if (query) searchTerm = query;
  if (tag) activeTag = tag;
  if (els.searchInput) els.searchInput.value = searchTerm;
}

function bindEvents() {
  els.menuToggle?.addEventListener("click", () => {
    const isOpen = els.navLinks.classList.toggle("is-open");
    document.body.classList.toggle("menu-open", isOpen);
    els.menuToggle.setAttribute("aria-expanded", String(isOpen));
  });

  els.navLinks?.addEventListener("click", (event) => {
    if (event.target.matches("a")) {
      els.navLinks.classList.remove("is-open");
      document.body.classList.remove("menu-open");
      els.menuToggle?.setAttribute("aria-expanded", "false");
    }
  });

  els.openCart?.addEventListener("click", openCart);
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-close-cart]")) closeCart();
    const addButton = event.target.closest("[data-add]");
    if (addButton) addToCart(addButton.dataset.add);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeCart();
  });

  els.cartItems?.addEventListener("click", (event) => {
    const increase = event.target.closest("[data-increase]");
    const decrease = event.target.closest("[data-decrease]");
    const remove = event.target.closest("[data-remove]");
    if (increase) updateQuantity(increase.dataset.increase, 1);
    if (decrease) updateQuantity(decrease.dataset.decrease, -1);
    if (remove) removeFromCart(remove.dataset.remove);
  });

  els.filterButtons?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    activeCategory = button.dataset.category;
    renderFilterButtons();
    renderProducts();
  });

  els.tagButtons?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tag]");
    if (!button) return;
    activeTag = button.dataset.tag;
    renderFilterButtons();
    renderProducts();
  });

  els.searchInput?.addEventListener("input", (event) => {
    searchTerm = event.target.value;
    renderProducts();
  });

  els.clearFilters?.addEventListener("click", () => {
    activeCategory = "Todos";
    activeTag = "Todos";
    searchTerm = "";
    if (els.searchInput) els.searchInput.value = "";
    renderFilterButtons();
    renderProducts();
  });

  els.prevSlide?.addEventListener("click", () => {
    goToSlide(currentSlide - 1);
    resetSlideTimer();
  });
  els.nextSlide?.addEventListener("click", () => {
    goToSlide(currentSlide + 1);
    resetSlideTimer();
  });
  els.carouselDots?.addEventListener("click", (event) => {
    const dot = event.target.closest("[data-slide]");
    if (!dot) return;
    goToSlide(Number(dot.dataset.slide));
    resetSlideTimer();
  });

  els.sendOrder?.addEventListener("click", sendOrder);

  els.sucursalTrigger?.addEventListener("click", abrirSucursalModal);
  els.sucursalModalClose?.addEventListener("click", cerrarSucursalModal);
  els.sucursalModal?.addEventListener("click", (event) => {
    if (event.target === els.sucursalModal) cerrarSucursalModal();
  });
  els.sucursalList?.addEventListener("click", (event) => {
    const option = event.target.closest("[data-sucursal-id]");
    if (!option) return;
    seleccionarSucursal(Number(option.dataset.sucursalId));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && els.sucursalModal && !els.sucursalModal.hidden) cerrarSucursalModal();
  });
}

async function resolverSucursalPublica() {
  const res = await fetch("/api/sucursales/");
  if (!res.ok) throw new Error("No se pudieron cargar las sucursales");
  sucursales = await res.json();

  const guardada = localStorage.getItem(SUCURSAL_KEY);
  const guardadaValida = guardada && sucursales.some((s) => String(s.id) === guardada);

  if (guardadaValida) {
    sucursalActual = Number(guardada);
    return;
  }

  // La sucursal guardada ya no existe o esta desactivada: se descarta y
  // se vuelve a elegir automaticamente (primera sucursal activa disponible).
  localStorage.removeItem(SUCURSAL_KEY);
  sucursalActual = sucursales.length ? sucursales[0].id : null;
  if (sucursalActual) localStorage.setItem(SUCURSAL_KEY, String(sucursalActual));
}

function nombreSucursalActual() {
  const sucursal = sucursales.find((s) => s.id === sucursalActual);
  if (!sucursal) return "Sin sucursales disponibles";
  // Preferimos la direccion (mas util para el cliente para ubicarse) y
  // caemos al nombre solo si la sucursal todavia no tiene direccion cargada.
  return sucursal.address && sucursal.address.trim() ? sucursal.address : sucursal.name;
}

function renderSucursalUI() {
  if (els.sucursalActualLabel) els.sucursalActualLabel.textContent = nombreSucursalActual();

  // Con 0 o 1 sucursal no tiene sentido abrir un modal a elegir: el boton
  // queda deshabilitado y sin flechita, para que no parezca un selector -
  // el visitante solo ve la direccion como texto informativo antes del
  // carrito. Con 2+ sucursales se habilita y aparece la flechita.
  const haySeleccionPosible = sucursales.length > 1;
  if (els.sucursalTrigger) {
    els.sucursalTrigger.disabled = !haySeleccionPosible;
    els.sucursalTrigger.setAttribute("aria-haspopup", haySeleccionPosible ? "dialog" : "false");
  }
  if (els.sucursalTriggerCaret) els.sucursalTriggerCaret.hidden = !haySeleccionPosible;

  if (!els.sucursalList) return;
  els.sucursalList.innerHTML = sucursales.length
    ? sucursales.map((s) => `
        <li>
          <button type="button" class="sucursal-option ${s.id === sucursalActual ? "is-active" : ""}" data-sucursal-id="${s.id}">
            <span>${s.name}</span>
            <span class="check" aria-hidden="true">✓ Seleccionada</span>
          </button>
        </li>
      `).join("")
    : `<li class="sucursal-modal-empty">No hay sucursales disponibles en este momento.</li>`;
}

function abrirSucursalModal() {
  if (!els.sucursalModal || els.sucursalTrigger?.disabled) return;
  els.sucursalModal.hidden = false;
  els.sucursalTrigger?.setAttribute("aria-expanded", "true");
}

function cerrarSucursalModal() {
  if (!els.sucursalModal) return;
  els.sucursalModal.hidden = true;
  els.sucursalTrigger?.setAttribute("aria-expanded", "false");
}

async function seleccionarSucursal(id) {
  if (id === sucursalActual) {
    cerrarSucursalModal();
    return;
  }
  sucursalActual = id;
  localStorage.setItem(SUCURSAL_KEY, String(sucursalActual));
  cerrarSucursalModal();
  renderSucursalUI();
  try {
    await loadCatalogData();
  } catch (error) {
    console.error("Error al cambiar de sucursal:", error);
    showLoadError();
    return;
  }
  applyUrlFilters();
  renderCategories();
  renderHomeProducts();
  renderFilterButtons();
  renderProducts();
  renderCart();
}

async function loadCatalogData() {
  const [productsRes, categoriesRes] = await Promise.all([
    fetch(`/api/productos/?sucursal=${sucursalActual}`),
    fetch(`/api/categorias/?sucursal=${sucursalActual}`),
  ]);
  if (!productsRes.ok || !categoriesRes.ok) throw new Error("Respuesta invalida del servidor");
  products = await productsRes.json();
  categories = await categoriesRes.json();
}

function showLoadError(texto) {
  const message = `<p class="product-card product-body">${texto || "No se pudieron cargar los productos. Intenta nuevamente."}</p>`;
  if (els.productGrid) els.productGrid.innerHTML = message;
  if (els.bestSellerGrid) els.bestSellerGrid.innerHTML = message;
  if (els.offerGrid) els.offerGrid.innerHTML = message;
  if (els.categoryCards) els.categoryCards.innerHTML = message;
  if (els.resultCount) els.resultCount.textContent = "";
}

async function init() {
  renderCarousel();
  renderCart();
  bindEvents();

  try {
    await resolverSucursalPublica();
    renderSucursalUI();
    if (!sucursalActual) {
      showLoadError("No hay sucursales disponibles en este momento.");
      return;
    }
    await loadCatalogData();
  } catch (error) {
    console.error("Error al cargar productos desde Django:", error);
    showLoadError();
    return;
  }

  applyUrlFilters();
  renderCategories();
  renderHomeProducts();
  renderFilterButtons();
  renderProducts();
  // Vuelve a pintar el carrito ahora que "products" tiene los datos vigentes
  // (al arrancar, renderCart() ya se llamo una vez con products vacio, asi
  // que un carrito con items viejos en localStorage seguia mostrando su
  // imagen cacheada hasta este segundo render).
  renderCart();
}

init();