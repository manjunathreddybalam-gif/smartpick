const money = value => new Intl.NumberFormat("en-IN", {style:"currency", currency:"INR", maximumFractionDigits:0}).format(Number(value || 0));
const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const safeURL = value => {
  try { const u = new URL(value, window.location.origin); return ["http:","https:"].includes(u.protocol) ? u.href : ""; }
  catch { return ""; }
};

async function getCSRFToken() {
  const response = await fetch("/admin/csrf-token");
  const data = await response.json();

  if (!response.ok || !data.csrf_token) {
    throw new Error("Could not get security token. Please log in again.");
  }

  return data.csrf_token;
}
let allProducts = [];
let compared = new Set();

async function fetchProducts() {
  const params = new URLSearchParams();
  const q = document.getElementById("search-input")?.value.trim();
  const category = document.getElementById("category-filter")?.value;
  const maxPrice = document.getElementById("price-filter")?.value;
  const sort = document.getElementById("sort-filter")?.value || "recommended";
  if (q) params.set("q", q);
  if (category && category !== "All") params.set("category", category);
  if (maxPrice) params.set("max_price", maxPrice);
  params.set("sort", sort);
  const response = await fetch(`/api/products?${params.toString()}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Could not load products");
  allProducts = data.products;
  const categorySelect = document.getElementById("category-filter");
  if (categorySelect && categorySelect.dataset.loaded !== "yes") {
    for (const categoryName of data.categories) {
      const option = document.createElement("option");
      option.value = categoryName; option.textContent = categoryName;
      categorySelect.appendChild(option);
    }
    categorySelect.dataset.loaded = "yes";
  }
  renderProducts(data.products);
  const total = document.getElementById("total-count");
  if (total) total.textContent = data.products.length;
}

function productCard(p) {
  const image = safeURL(p.image_url);
  const affiliate = safeURL(p.affiliate_url);
  const selected = compared.has(p.id);
  const features = String(p.features || "").split(";").map(s=>s.trim()).filter(Boolean).slice(0,3);
  return `<article class="product-card">
    <div class="product-image-wrap">
      ${image ? `<img class="product-image" src="${escapeHTML(image)}" alt="${escapeHTML(p.name)}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='grid'">` : ""}
      <div class="image-fallback" ${image ? 'style="display:none"' : ""}>✧</div>
      ${p.tag ? `<span class="product-tag">${escapeHTML(p.tag)}</span>` : ""}
      <button class="compare-check ${selected ? "selected" : ""}" data-compare="${p.id}" aria-label="Compare ${escapeHTML(p.name)}">${selected ? "✓" : "+"}</button>
    </div>
    <div class="product-info"><div class="product-meta"><span>${escapeHTML(p.category)}</span><span class="rating">★ ${Number(p.rating).toFixed(1)}</span></div>
      <h3>${escapeHTML(p.name)}</h3><p class="product-description">${escapeHTML(p.description)}</p>
      <div class="feature-list">${features.map(f=>`<span>${escapeHTML(f)}</span>`).join("")}</div>
      <div class="product-bottom"><div><small>Listed price</small><strong>${money(p.price)}</strong></div>
      ${affiliate ? `<a class="buy-btn" href="${escapeHTML(affiliate)}" target="_blank" rel="sponsored nofollow noopener">View deal ↗</a>` : `<span class="no-link">Link not added</span>`}</div>
    </div></article>`;
}

function renderProducts(products) {
  const grid = document.getElementById("product-grid");
  if (!grid) return;
  grid.innerHTML = products.map(productCard).join("");
  const empty = document.getElementById("empty-state");
  empty?.classList.toggle("hidden", products.length !== 0);
  grid.classList.toggle("hidden", products.length === 0);
  document.getElementById("compare-count")?.replaceChildren(document.createTextNode(compared.size));
  grid.querySelectorAll("[data-compare]").forEach(btn => btn.addEventListener("click", () => {
    const id = Number(btn.dataset.compare);
    if (compared.has(id)) compared.delete(id);
    else if (compared.size < 3) compared.add(id);
    else { alert("You can compare up to 3 products at a time."); return; }
    renderProducts(products);
  }));
}

function openCompare() {
  const picked = allProducts.filter(p => compared.has(p.id));
  const modal = document.getElementById("compare-modal");
  if (!modal) return;
  if (!picked.length) { alert("Select at least one product using the + button."); return; }
  document.getElementById("compare-content").innerHTML = `<div class="comparison-table"><table><thead><tr><th>Details</th>${picked.map(p=>`<th>${escapeHTML(p.name)}</th>`).join("")}</tr></thead><tbody>
  <tr><td>Price</td>${picked.map(p=>`<td><strong>${money(p.price)}</strong></td>`).join("")}</tr>
  <tr><td>Rating</td>${picked.map(p=>`<td>★ ${Number(p.rating).toFixed(1)} / 5</td>`).join("")}</tr>
  <tr><td>Category</td>${picked.map(p=>`<td>${escapeHTML(p.category)}</td>`).join("")}</tr>
  <tr><td>Description</td>${picked.map(p=>`<td>${escapeHTML(p.description)}</td>`).join("")}</tr>
  <tr><td>Features</td>${picked.map(p=>`<td>${escapeHTML(String(p.features).split(";").join(", "))}</td>`).join("")}</tr>
  <tr><td>Seller link</td>${picked.map(p=>`<td>${safeURL(p.affiliate_url) ? `<a target="_blank" rel="sponsored nofollow noopener" href="${escapeHTML(safeURL(p.affiliate_url))}">View ↗</a>` : "Not added"}</td>`).join("")}</tr>
  </tbody></table></div>`;
  modal.classList.remove("hidden");
}

function initHome() {
  if (!document.getElementById("product-grid")) return;
  let debounce;
  ["search-input","category-filter","price-filter","sort-filter"].forEach(id => {
    const el = document.getElementById(id);
    el?.addEventListener(id === "search-input" ? "input" : "change", () => {
      clearTimeout(debounce); debounce = setTimeout(() => fetchProducts().catch(showHomeError), id === "search-input" ? 250 : 0);
    });
  });
  document.getElementById("clear-filters")?.addEventListener("click", () => {
    document.getElementById("search-input").value = "";
    document.getElementById("category-filter").value = "All";
    document.getElementById("price-filter").value = "";
    document.getElementById("sort-filter").value = "recommended";
    fetchProducts().catch(showHomeError);
  });
  document.getElementById("compare-toggle")?.addEventListener("click", openCompare);
  document.getElementById("close-modal")?.addEventListener("click", () => document.getElementById("compare-modal").classList.add("hidden"));
  document.getElementById("compare-modal")?.addEventListener("click", e => { if (e.target.id === "compare-modal") e.currentTarget.classList.add("hidden"); });
  document.getElementById("year").textContent = new Date().getFullYear();
  fetchProducts().catch(showHomeError);
}
function showHomeError(error) {
  const grid = document.getElementById("product-grid");
  if (grid) grid.innerHTML = `<p class="error-text">Could not load products. Is the Flask server running? ${escapeHTML(error.message)}</p>`;
}

function initAdmin() {
  const form = document.getElementById("product-form");
  if (!form) return;
  const ids = ["name","category","price","rating","description","features","image_url","affiliate_url","tag"];
  const val = id => document.getElementById(id).value;
  const message = (text, isError=false) => {
    const box = document.getElementById("admin-message");
    box.textContent = text; box.classList.remove("hidden","error"); if (isError) box.classList.add("error");
    window.scrollTo({top:0, behavior:"smooth"});
  };
  const reset = () => {
    form.reset(); document.getElementById("product-id").value = "";
    document.getElementById("rating").value = "4"; document.getElementById("price").value = "0";
    document.getElementById("form-title").textContent = "Add a product";
    document.getElementById("save-btn").innerHTML = "Save product <span>↗</span>";
  };
  async function loadAdmin() {
    const response = await fetch("/api/products");
    const data = await response.json();
    const list = document.getElementById("admin-list");
    document.getElementById("admin-count").textContent = `${data.products.length} products`;
    list.innerHTML = data.products.map(p => `<article class="admin-product">
      <div class="admin-product-copy"><strong>${escapeHTML(p.name)}</strong><span>${escapeHTML(p.category)} · ${money(p.price)} · ★ ${Number(p.rating).toFixed(1)}</span></div>
      <div class="admin-actions"><button class="small-btn" data-edit="${p.id}">Edit</button><button class="small-btn danger-btn" data-delete="${p.id}">Delete</button></div>
    </article>`).join("") || "<p>No products yet. Add your first product above.</p>";
    list.querySelectorAll("[data-edit]").forEach(btn => btn.addEventListener("click", () => {
      const p = data.products.find(item => item.id === Number(btn.dataset.edit));
      if (!p) return;
      document.getElementById("product-id").value = p.id;
      ids.forEach(id => document.getElementById(id).value = p[id] ?? "");
      document.getElementById("form-title").textContent = "Edit product";
      document.getElementById("save-btn").innerHTML = "Update product <span>↗</span>";
      window.scrollTo({top:0,behavior:"smooth"});
    }));
    list.querySelectorAll("[data-delete]").forEach(btn => btn.addEventListener("click", async () => {
      const p = data.products.find(item => item.id === Number(btn.dataset.delete));
      if (!p || !confirm(`Delete "${p.name}"? This cannot be undone.`)) return;
      const csrfToken = await getCSRFToken();
      const res = await fetch(`/api/products/${p.id}`, {
        method: "DELETE",
        headers: {"X-CSRF-Token": csrfToken}
});
      const result = await res.json();
      if (!res.ok) return message(result.error || "Delete failed", true);
      message("Product deleted."); loadAdmin();
    }));
  }
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const data = Object.fromEntries(ids.map(id => [id, val(id)]));
    data.price = Number(data.price); data.rating = Number(data.rating);
    const id = document.getElementById("product-id").value;
    const csrfToken = await getCSRFToken();
const res = await fetch(id ? `/api/products/${id}` : "/api/products", {
  method: id ? "PUT" : "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-Token": csrfToken
  },
  body: JSON.stringify(data)
});
    const result = await res.json();
    if (!res.ok) return message(result.error || "Could not save product", true);
    message(id ? "Product updated." : "Product added.");
    reset(); loadAdmin();
  });
  document.getElementById("reset-form").addEventListener("click", reset);
  loadAdmin().catch(err => message(err.message, true));
}
document.addEventListener("DOMContentLoaded", () => { initHome(); initAdmin(); });
