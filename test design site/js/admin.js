/* =============================================
   HRz PITSTOP – Admin CMS & Control Center Module
   Dashboard UI Redesign
   ============================================= */

window.HRz = window.HRz || {};

class AdminCMS {
  static activeTab = "hero";
  static catalogPage = 1;
  static catalogSearch = "";
  static catalogStockFilter = "All";
  static catalogSearchTimer = null;
  static editingProductId = null;
  static savedProductId = null;
  static savedOrderId = null;
  static orderSearch = "";
  static adminGateMessage = "";

  // If the DB cache now holds the edited products (i.e. the db.js
  // persistence fix has landed), the "session only" banner that
  // DB.markCatalogUnsaved() adds is stale, so remove it. If the
  // products cache key is absent, leave the banner: the honest
  // warning is that the edit is session-only.
  static _clearUnsavedBannerIfPersisted() {
    try {
      if (localStorage.getItem("hrz_db_products_v31")) {
        const banner = document.getElementById("unsaved-catalog-banner");
        if (banner) banner.remove();
      }
    } catch {}
  }

  // Shared validation for product price/name edits. Price must be a
  // non-negative number; an empty name is rejected. Returns
  // { ok, price, error } and never invents a value.
  static _validateProductEdit(name, priceRaw) {
    if (!String(name || "").trim()) {
      return { ok: false, error: "Product name cannot be empty." };
    }
    if (priceRaw === "" || priceRaw === null || priceRaw === undefined) {
      return { ok: false, error: "Price is required and must be a non-negative number." };
    }
    const price = Number(priceRaw);
    if (!Number.isFinite(price) || price < 0) {
      return { ok: false, error: "Price must be a non-negative number." };
    }
    return { ok: true, price };
  }

  // Order statuses offered in the admin panel, in checkout flow
  // order: a new checkout order starts as "Pending WhatsApp
  // Confirmation", then Confirmed -> Shipped -> Delivered. The
  // current status is always included as an option, even if it is
  // a legacy value (e.g. "In Transit"), so the select never
  // misdisplays an order's real status (previously a Pending order
  // showed as "Order Placed" because no option matched it).
  static orderStatusOptions(currentStatus) {
    const flow = [
      "Pending WhatsApp Confirmation",
      "Confirmed",
      "Shipped",
      "Delivered",
      "Cancelled",
      "Order Placed",
      "Processing & Fitment Checked"
    ];
    const list = flow.includes(currentStatus) ? flow : [currentStatus, ...flow];
    const escapeHTML = window.HRz.Utils.escapeHTML;
    return list.map(st => `<option value="${escapeHTML(st)}" ${st === currentStatus ? "selected" : ""}>${escapeHTML(st)}</option>`).join("");
  }

  static render(container) {
    // ---- ADMIN GATE: no admin UI renders until both checks pass. ----
    const Auth = window.HRz.Auth;
    if (!Auth || !Auth.isLoggedIn() || !Auth.isAdminUnlocked()) {
      this.renderAdminGate(container);
      return;
    }
    const db = window.HRz.DB;
    const storage = window.HRz.Storage;
    const utils = window.HRz.Utils;
    const escapeHTML = utils.escapeHTML;

    const products = db.getProducts();
    const compatibility = db.getCompatibility();
    const bikes = db.getBikes();
    const reviews = db.getReviews();
    const orders = db.getOrders();
    const auditLogs = storage.getAuditLogs();
    const heroBanner = storage.getHeroBanner();

    const pendingReviews = reviews.filter(r => r.status === 'pending').length;

    container.innerHTML = `
      <div class="admin-dashboard-layout">
        <!-- Sidebar Navigation -->
        <aside class="admin-sidebar">
          <div class="admin-sidebar-header">
            <p class="eyebrow">HRz PITSTOP</p>
            <h2>Admin Center</h2>
          </div>
          <div class="admin-tabs-list">
            <button class="admin-tab-btn ${this.activeTab === "hero" ? "active" : ""}" data-tab="hero">
              🎯 Hero Offer Banner
            </button>
            <button class="admin-tab-btn ${this.activeTab === "catalog" ? "active" : ""}" data-tab="catalog">
              📦 Product Catalog <span class="badge">${products.length}</span>
            </button>
            <button class="admin-tab-btn ${this.activeTab === "compatibility" ? "active" : ""}" data-tab="compatibility">
              🏍️ Compatibility Matrix <span class="badge">${compatibility.length}</span>
            </button>
            <button class="admin-tab-btn ${this.activeTab === "reviews" ? "active" : ""}" data-tab="reviews">
              ⭐ Moderation Queue ${pendingReviews > 0 ? `<span class="badge" style="background:var(--gold);color:#000;">${pendingReviews}</span>` : ""}
            </button>
            <button class="admin-tab-btn ${this.activeTab === "orders" ? "active" : ""}" data-tab="orders">
              📜 Customer Orders <span class="badge">${orders.length}</span>
            </button>
            <button class="admin-tab-btn ${this.activeTab === "csv" ? "active" : ""}" data-tab="csv">
              📊 CSV Import/Export
            </button>
            <button class="admin-tab-btn ${this.activeTab === "logs" ? "active" : ""}" data-tab="logs">
              ⏱️ Audit Logs
            </button>
          </div>
        </aside>

        <!-- Main Content Area -->
        <main class="admin-main">
          <!-- Topbar -->
          <div class="admin-topbar">
            <div class="admin-page-title">
              <h1>${this.getPageTitle(this.activeTab)}</h1>
              <p class="admin-topbar-user">Signed in — admin unlocked for this tab only</p>
            </div>
            <button class="small-action-btn admin-lock-btn" id="adminLockBtn">🔒 Lock admin</button>
          </div>

          <!-- Tab Content -->
          <div class="admin-tab-content">
            ${this.renderTabContent(this.activeTab, { products, compatibility, bikes, reviews, orders, auditLogs, heroBanner })}
          </div>
        </main>
      </div>
    `;

    container.querySelectorAll(".admin-tab-btn").forEach(btn => {
      btn.onclick = () => {
        this.activeTab = btn.dataset.tab;
        this.render(container);
      };
    });

    this.bindTabEvents(container);
  }

  // Gate screen ONLY — renders no product, order, review or catalogue
  // data. Three states: (a) not signed in -> sign-in button (the
  // existing Auth popup; a guest sign-in still fails the gate because
  // isLoggedIn() stays false for guests); (b) signed in, no PIN stored
  // yet -> set-PIN form (first-run only); (c) signed in, PIN stored
  // -> enter-PIN form. A wrong PIN shows an error and nothing else.
  static renderAdminGate(container) {
    const Auth = window.HRz.Auth;
    if (!Auth) {
      container.innerHTML = `<div class="admin-gate-wrap"><div class="admin-gate-card"><h1>Admin panel unavailable</h1><p class="admin-gate-text">The sign-in service did not load. Reload the page and try again.</p><p><a href="#home">← Back to the store</a></p></div></div>`;
      return;
    }
    const utils = window.HRz.Utils;
    const escapeHTML = utils.escapeHTML;
    const msg = this.adminGateMessage;
    this.adminGateMessage = "";
    const signedIn = Auth && Auth.isLoggedIn();
    const user = signedIn ? Auth.getUser() : null;
    const hasPin = Auth ? Auth.hasAdminPin() : false;

    let body = "";
    if (!signedIn) {
      body = `
        <p class="admin-gate-text">The admin panel needs a signed-in account. Guest checkout access does not open it.</p>
        <button class="accent-button admin-gate-btn" id="adminGateSigninBtn">Sign in to continue</button>
        <p class="admin-gate-text small">Signed in already in another tab? Reload this page and the panel will check again.</p>`;
    } else if (!hasPin) {
      body = `
        <p class="admin-gate-text">Signed in as <strong>${escapeHTML(user.name || user.email || "admin")}</strong>. No admin PIN exists in this browser yet, so set one now. It is stored in this browser only.</p>
        <form id="adminSetPinForm" class="admin-gate-form">
          <label for="adminNewPin">New admin PIN (4–8 digits)</label>
          <input type="password" id="adminNewPin" inputmode="numeric" autocomplete="new-password" required minlength="4" maxlength="8" placeholder="••••" />
          <label for="adminNewPinConfirm">Confirm admin PIN</label>
          <input type="password" id="adminNewPinConfirm" inputmode="numeric" autocomplete="new-password" required minlength="4" maxlength="8" placeholder="••••" />
          <p class="admin-gate-error" id="adminGateError" role="alert"></p>
          <button type="submit" class="accent-button admin-gate-btn">Set PIN &amp; open admin panel</button>
        </form>`;
    } else {
      body = `
        <p class="admin-gate-text">Signed in as <strong>${escapeHTML(user.name || user.email || "admin")}</strong>. Enter the admin PIN for this browser.</p>
        <form id="adminEnterPinForm" class="admin-gate-form">
          <label for="adminPinInput">Admin PIN</label>
          <input type="password" id="adminPinInput" inputmode="numeric" autocomplete="current-password" required minlength="4" maxlength="8" placeholder="••••" />
          <p class="admin-gate-error" id="adminGateError" role="alert"></p>
          <button type="submit" class="accent-button admin-gate-btn">Unlock admin panel</button>
        </form>
        <button class="small-action-btn admin-gate-btn" id="adminGateSignoutBtn">Sign out</button>`;
    }

    container.innerHTML = `
      <div class="admin-gate-wrap">
        <div class="admin-gate-card">
          <p class="eyebrow">HRz PITSTOP</p>
          <h1>Admin panel locked</h1>
          ${msg ? `<p class="admin-gate-error" role="alert">${escapeHTML(msg)}</p>` : ""}
          ${body}
          <p class="admin-gate-notice">Client-side lock only: this static site has no server, so this PIN is a deterrent, not real security. Anyone with access to this browser can inspect or clear its stored data and bypass it. There is no default PIN.</p>
          <p><a href="#home">← Back to the store</a></p>
        </div>
      </div>`;

    const signinBtn = container.querySelector("#adminGateSigninBtn");
    if (signinBtn) {
      signinBtn.onclick = () => {
        Auth.showLoginPopup(
          () => {
            // Guest sign-in runs this callback WITHOUT creating a user,
            // so re-check: only a real sign-in passes the gate.
            if (Auth.isLoggedIn()) { this.render(container); }
            else {
              this.adminGateMessage = "Guest access cannot open the admin panel. Please sign in with an account.";
              this.render(container);
            }
          },
          () => {
            this.adminGateMessage = "Sign-in cancelled. The admin panel was not opened.";
            this.render(container);
          }
        );
      };
    }
    const setForm = container.querySelector("#adminSetPinForm");
    if (setForm) {
      setForm.onsubmit = (e) => {
        e.preventDefault();
        const err = container.querySelector("#adminGateError");
        Auth.setAdminPin(
          container.querySelector("#adminNewPin").value.trim(),
          container.querySelector("#adminNewPinConfirm").value.trim()
        ).then(res => {
          if (res.ok) { this.render(container); }
          else if (err) { err.textContent = res.error; }
        });
      };
    }
    const enterForm = container.querySelector("#adminEnterPinForm");
    if (enterForm) {
      enterForm.onsubmit = (e) => {
        e.preventDefault();
        const err = container.querySelector("#adminGateError");
        Auth.verifyAdminPin(container.querySelector("#adminPinInput").value.trim()).then(ok => {
          if (ok) { this.render(container); }
          else if (err) { err.textContent = "Wrong PIN — the admin panel was not opened."; }
        });
      };
    }
    const signoutBtn = container.querySelector("#adminGateSignoutBtn");
    if (signoutBtn) {
      signoutBtn.onclick = () => { Auth.logout(); this.render(container); };
    }
  }

  static getPageTitle(tab) {
    const titles = {
      hero: "Hero Promotional Banner",
      catalog: "Product Catalog Management",
      compatibility: "Bike Compatibility Matrix",
      reviews: "Review Moderation Queue",
      orders: "Customer Orders",
      csv: "Bulk Data Tools",
      logs: "System Audit Logs"
    };
    return titles[tab] || "Dashboard";
  }

  static renderTabContent(tab, data) {
    const utils = window.HRz.Utils;
    const db = window.HRz.DB;
    const escapeHTML = utils.escapeHTML;

    if (tab === "hero") {
      const hero = data.heroBanner;
      return `
        <div class="admin-panel-card">
          <div class="cms-toolbar">
            <div>
              <h3>Customize Homepage Hero</h3>
              <p>Change the main headline, promotional offer badge, and background banner image.</p>
            </div>
          </div>

          <form id="heroCmsForm" class="admin-form-grid">
            <div class="form-group">
              <label for="heroBadgeInput">Promotional Offer Badge *</label>
              <input type="text" id="heroBadgeInput" value="${escapeHTML(hero.badge || '')}" required placeholder="e.g. MONSOON MEGA SALE · FLAT 20% OFF" />
            </div>

            <div class="form-group">
              <label for="heroTitleInput">Main Hero Headline *</label>
              <input type="text" id="heroTitleInput" value="${escapeHTML(hero.title || '')}" required placeholder="e.g. Guaranteed Fitment for Your Motorcycle" />
            </div>

            <div class="form-group admin-form-full">
              <label for="heroSubheadInput">Subhead Explanation</label>
              <textarea id="heroSubheadInput" rows="2" required>${escapeHTML(hero.subtitle || '')}</textarea>
            </div>

            <div class="form-group admin-form-full">
              <label for="heroBgImageInput">Hero Background Image URL or Path *</label>
              <input type="text" id="heroBgImageInput" value="${escapeHTML(hero.bgImage || 'images/hero_banner.webp')}" required />
              
              <div class="image-preset-picker">
                <button type="button" class="preset-img-btn" data-url="images/hero-rider.webp">Default Rider PNG</button>
                <button type="button" class="preset-img-btn" data-url="images/hero_banner.webp">Hero Banner JPG</button>
                <button type="button" class="preset-img-btn" data-url="images/category_protection.webp">Protection Banner</button>
              </div>

              <div class="file-upload-row">
                <label for="heroBgFileUpload" class="small-action-btn" style="display:inline-block;">📤 Upload Custom Banner</label>
                <input type="file" id="heroBgFileUpload" accept="image/*" style="display:none;" />
              </div>
            </div>

            <div class="admin-form-full hero-preview-box">
              <h4>Live Banner Preview</h4>
              <div class="rider-hero" style="background: linear-gradient(135deg, rgba(9, 10, 12, 0.85), rgba(9, 10, 12, 0.95)), url('${escapeHTML(hero.bgImage)}') center/cover no-repeat;">
                <div class="hero-content-box">
                  <span class="hero-badge" id="previewBadge">${escapeHTML(hero.badge)}</span>
                  <h1 class="hero-headline" id="previewTitle">${escapeHTML(hero.title)}</h1>
                  <p class="hero-subhead" id="previewSubhead">${escapeHTML(hero.subtitle)}</p>
                </div>
              </div>
            </div>

            <div class="admin-form-full" style="margin-top:16px;">
              <button type="submit" class="accent-button">Save & Publish Hero Banner</button>
            </div>
          </form>
        </div>
      `;
    }

    if (tab === "catalog") {
      const activeCategoryFilter = document.getElementById("app")?.dataset.catalogFilter || "All";
      const categories = ["All", ...window.HRz.DB.getCategories()];
      
      let filteredProducts = data.products;
      if (activeCategoryFilter !== "All") {
        filteredProducts = filteredProducts.filter(p => p.category === activeCategoryFilter);
      }
      
      if (this.catalogSearch) {
        const query = this.catalogSearch.toLowerCase();
        filteredProducts = filteredProducts.filter(p => 
          p.name.toLowerCase().includes(query) || 
          (p.sku && p.sku.toLowerCase().includes(query)) ||
          (p.category && p.category.toLowerCase().includes(query))
        );
      }

      if (this.catalogStockFilter === "In Stock") {
        filteredProducts = filteredProducts.filter(p => p.inStock);
      } else if (this.catalogStockFilter === "Out of Stock") {
        filteredProducts = filteredProducts.filter(p => !p.inStock);
      }

      const itemsPerPage = 50;
      const totalPages = Math.ceil(filteredProducts.length / itemsPerPage) || 1;
      if (this.catalogPage > totalPages) this.catalogPage = totalPages;
      if (this.catalogPage < 1) this.catalogPage = 1;
      
      const startIndex = (this.catalogPage - 1) * itemsPerPage;
      const paginatedProducts = filteredProducts.slice(startIndex, startIndex + itemsPerPage);

      return `
        <!-- Metrics Row -->
        <div class="admin-metrics-row">
          <div class="admin-metric-card">
            <span class="title">Total Products</span>
            <span class="value">${data.products.length}</span>
          </div>
          <div class="admin-metric-card">
            <span class="title">Categories</span>
            <span class="value">${categories.length - 1}</span>
          </div>
          <div class="admin-metric-card">
            <span class="title">Low Stock Alerts</span>
            <span class="value" style="color:var(--gold);">0</span>
          </div>
        </div>

        <div class="admin-panel-card">
          <div class="cms-toolbar">
            <div>
              <h3>Product Inventory</h3>
            </div>
            <div class="admin-toolbar-actions">
              <button class="accent-button" id="exportCatalogBtn">📥 Export JSON</button>
              <button class="accent-button" id="addNewProductBtn">+ Add New Product</button>
              <button class="small-action-btn danger admin-reset-btn" id="resetCatalogBtn" title="Re-fetch the original catalogue and discard saved product edits in this browser">↺ Reset to original catalogue</button>
            </div>
          </div>
          
          <div class="admin-search-row">
            <input type="search" id="adminCatalogSearchInput" value="${escapeHTML(this.catalogSearch)}" placeholder="Search products by name, SKU or category..." aria-label="Search products" />
            <label class="admin-search-label" for="adminStockFilter">Stock</label>
            <select id="adminStockFilter" aria-label="Filter by stock status">
              <option value="All" ${this.catalogStockFilter === "All" ? "selected" : ""}>All stock</option>
              <option value="In Stock" ${this.catalogStockFilter === "In Stock" ? "selected" : ""}>In stock only</option>
              <option value="Out of Stock" ${this.catalogStockFilter === "Out of Stock" ? "selected" : ""}>Out of stock only</option>
            </select>
          </div>
          <p class="admin-result-count">Showing ${filteredProducts.length} of ${data.products.length} products${this.catalogSearch ? ` for “${escapeHTML(this.catalogSearch)}”` : ""}. Tip: use Quick edit on a row to change its price or stock status without opening the full form.</p>

          <div class="category-filter-pills" style="margin-bottom: 24px; display: flex; gap: 8px; flex-wrap: wrap;">
            ${categories.map(cat => `
              <button class="filter-pill admin-cat-filter ${activeCategoryFilter === cat ? "active" : ""}" data-filter="${escapeHTML(cat)}" style="padding: 6px 14px; border: 1px solid #333; border-radius: 20px; background: ${activeCategoryFilter === cat ? 'var(--red)' : '#1a1c1e'}; color: white; cursor:pointer; font-size:12px;">${escapeHTML(cat)}</button>
            `).join("")}
          </div>

          <div class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Image</th>
                  <th>Name & SKU</th>
                  <th>Category</th>
                  <th>Price (INR)</th>
                  <th>Stock</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${paginatedProducts.map(p => `
                  <tr>
                    <td><img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" width="44" height="44" style="object-fit:cover; border-radius:6px; border:1px solid #333;" onerror="this.src='images/helmet_product.webp'" /></td>
                    <td><strong>${escapeHTML(p.name)}</strong> ${p.isVisible === false ? '<span style="color:var(--red); font-size:10px; border:1px solid var(--red); padding:2px 4px; border-radius:3px; margin-left:4px;">HIDDEN</span>' : ''}<br/><small style="color:#888;">SKU: ${escapeHTML(p.sku)}</small></td>
                    <td><span class="cat-tag">${escapeHTML(p.category)}</span></td>
                    <td>${this.editingProductId === p.id ? `<input type="number" min="0" step="any" class="admin-inline-price" data-edit-price="${escapeHTML(p.id)}" value="${p.price}" aria-label="Price for ${escapeHTML(p.name)}" />` : utils.formatCurrency(p.price)}</td>
                    <td>${this.editingProductId === p.id ? `<select class="admin-inline-stock" data-edit-stock="${escapeHTML(p.id)}" aria-label="Stock status for ${escapeHTML(p.name)}"><option value="true" ${p.inStock ? "selected" : ""}>In Stock</option><option value="false" ${!p.inStock ? "selected" : ""}>Out of Stock</option></select>` : (p.inStock ? "<span class='stock-tag in'>In Stock</span>" : "<span class='stock-tag out'>Out of Stock</span>")}</td>
                    <td>
                      ${this.editingProductId === p.id ? `
                        <button class="small-action-btn admin-save-btn" data-id="${escapeHTML(p.id)}">Save</button>
                        <button class="small-action-btn admin-cancel-btn" data-id="${escapeHTML(p.id)}">Cancel</button>
                      ` : `
                        <button class="small-action-btn admin-quickedit-btn" data-id="${escapeHTML(p.id)}">Quick edit</button>
                        <button class="small-action-btn edit-prod-btn" data-id="${escapeHTML(p.id)}">Edit</button>
                        <button class="small-action-btn delete-prod-btn danger" data-id="${escapeHTML(p.id)}">Delete</button>
                      `}
                      ${this.savedProductId === p.id ? '<span class="admin-saved-badge">✓ Saved</span>' : ''}
                    </td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
          
          <div class="admin-pagination" style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #333;">
            <button class="small-action-btn" id="prevCatPageBtn" ${this.catalogPage <= 1 ? 'disabled' : ''} style="cursor: ${this.catalogPage <= 1 ? 'not-allowed' : 'pointer'}; opacity: ${this.catalogPage <= 1 ? '0.5' : '1'};">&laquo; Prev</button>
            <span style="color: #aaa; font-size: 14px;">Page ${this.catalogPage} of ${totalPages}</span>
            <button class="small-action-btn" id="nextCatPageBtn" ${this.catalogPage >= totalPages ? 'disabled' : ''} style="cursor: ${this.catalogPage >= totalPages ? 'not-allowed' : 'pointer'}; opacity: ${this.catalogPage >= totalPages ? '0.5' : '1'};">Next &raquo;</button>
          </div>
        </div>
      `;
    }

    if (tab === "compatibility") {
      return `
        <div class="admin-panel-card">
          <div class="cms-toolbar">
            <div>
              <h3>Fitment Rules</h3>
              <p>Manage product compatibility with specific motorcycles.</p>
            </div>
            <button class="accent-button" id="addCompRuleBtn">+ Add Fitment Rule</button>
          </div>
          <div class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Rule ID</th>
                  <th>Product</th>
                  <th>Compatible Bike</th>
                  <th>Fit Type</th>
                  <th>Notes</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${data.compatibility.map(c => {
                  const prod = db.getProductById(c.productId);
                  const bike = data.bikes.find(b => b.id === c.bikeId);
                  return `
                    <tr>
                      <td><code style="color:#888;">${c.id}</code></td>
                      <td><strong>${prod ? escapeHTML(prod.name) : escapeHTML(c.productId)}</strong></td>
                      <td>${bike ? `${escapeHTML(bike.brand)} ${escapeHTML(bike.model)}` : "Universal"}</td>
                      <td><span class="cat-tag">${escapeHTML(c.fitType)}</span></td>
                      <td><small style="color:#888;">${escapeHTML(c.notes || "N/A")}</small></td>
                      <td>
                        <button class="small-action-btn delete-comp-btn danger" data-id="${escapeHTML(c.id)}">Delete</button>
                      </td>
                    </tr>
                  `;
                }).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    if (tab === "reviews") {
      return `
        <div class="admin-panel-card">
          <div class="cms-toolbar">
            <div>
              <h3>Customer Reviews Queue</h3>
              <p>Approve or reject customer installation reviews before they appear on the storefront.</p>
            </div>
          </div>
          <div class="reviews-moderation-grid">
            ${data.reviews.map(r => `
              <div class="moderation-card ${r.status}">
                <div class="mod-header">
                  <strong>${escapeHTML(r.reviewerName)}</strong>
                  <span class="status-badge ${r.status}">${escapeHTML(r.status.toUpperCase())}</span>
                </div>
                <p class="bike-info">Bike: ${escapeHTML(r.bikeName)}</p>
                <h4 class="title">${escapeHTML(r.title)}</h4>
                <p class="comment">"${escapeHTML(r.comment)}"</p>
                <div class="mod-actions">
                  ${r.status !== "published" ? `<button class="small-action-btn approve-rev-btn" data-id="${escapeHTML(r.id)}">Approve</button>` : ""}
                  ${r.status !== "rejected" ? `<button class="small-action-btn danger reject-rev-btn" data-id="${escapeHTML(r.id)}">Reject</button>` : ""}
                </div>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    if (tab === "orders") {
      const orderQuery = this.orderSearch.toLowerCase();
      const filteredOrders = orderQuery
        ? data.orders.filter(o => (o.id || "").toLowerCase().includes(orderQuery) || (o.trackingId || "").toLowerCase().includes(orderQuery))
        : data.orders;
      return `
        <div class="admin-panel-card">
          <div class="cms-toolbar">
            <div>
              <h3>Customer Orders</h3>
              <p>Process orders and update tracking statuses.</p>
            </div>
          </div>
          <div class="admin-search-row">
            <input type="search" id="adminOrderSearchInput" value="${escapeHTML(this.orderSearch)}" placeholder="Search orders by order ID or tracking ID..." aria-label="Search orders" />
          </div>
          <p class="admin-result-count">Showing ${filteredOrders.length} of ${data.orders.length} orders. Changing a status saves it immediately through the DB; the tracking page reads the same orders, so it shows the new status.</p>
          <div class="admin-table-wrapper">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Date</th>
                  <th>Bike Fitment</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${filteredOrders.map(o => `
                  <tr>
                    <td><strong>${escapeHTML(o.id)}</strong></td>
                    <td><small style="color:#888;">${escapeHTML(o.date)}</small></td>
                    <td>${escapeHTML(o.bike)}</td>
                    <td>${utils.formatCurrency(o.total)}</td>
                    <td>
                      <select class="order-status-select" data-id="${escapeHTML(o.id)}" aria-label="Status for order ${escapeHTML(o.id)}">
                        ${this.orderStatusOptions(o.status)}
                      </select>
                      <span class="admin-saved-badge">${this.savedOrderId === o.id ? "✓ Saved" : ""}</span>
                    </td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    if (tab === "csv") {
      return `
        <div class="admin-panel-card">
          <h3>CSV Import & Export</h3>
          <p style="color:var(--mute); font-size:14px; margin-bottom: 24px;">Export the full relational compatibility table or bulk upload new fitment rules via CSV.</p>
          
          <div style="display:flex; gap:16px;">
            <button class="accent-button" id="exportCsvBtn">📥 Download Compatibility CSV</button>
            <label for="importCsvInput" class="small-action-btn" style="padding:10px 16px; font-size:14px; display:inline-flex; align-items:center;">📤 Upload Compatibility CSV</label>
            <input type="file" id="importCsvInput" accept=".csv" style="display:none;" />
          </div>
        </div>
      `;
    }

    if (tab === "logs") {
      return `
        <div class="admin-panel-card">
          <h3>System Audit Logs</h3>
          <p style="color:var(--mute); font-size:14px; margin-bottom: 24px;">Track CMS changes and moderator actions.</p>
          
          <div class="audit-log-list">
            ${data.auditLogs.map(l => `
              <div class="log-item">
                <span class="log-time">${escapeHTML(new Date(l.timestamp).toLocaleTimeString())}</span>
                <strong class="log-user">${escapeHTML(l.user)}:</strong>
                <span class="log-text">${escapeHTML(l.action)}</span>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }
  }

  static bindTabEvents(container) {
    const db = window.HRz.DB;
    const storage = window.HRz.Storage;
    const utils = window.HRz.Utils;
    const appContainer = document.getElementById("app");

    // Lock admin (clears the tab-only unlock, then shows the gate)
    const lockBtn = container.querySelector("#adminLockBtn");
    if (lockBtn) {
      lockBtn.onclick = () => {
        if (window.HRz.Auth) window.HRz.Auth.lockAdmin();
        this.editingProductId = null;
        this.render(container);
      };
    }

    // Hero CMS Events
    const heroForm = container.querySelector("#heroCmsForm");
    if (heroForm) {
      const bgInput = container.querySelector("#heroBgImageInput");
      const fileInput = container.querySelector("#heroBgFileUpload");

      container.querySelectorAll(".preset-img-btn").forEach(btn => {
        btn.onclick = () => { bgInput.value = btn.dataset.url; };
      });

      if (fileInput) {
        fileInput.onchange = (e) => {
          const file = e.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (evt) => { bgInput.value = evt.target.result; };
            reader.readAsDataURL(file);
          }
        };
      }

      heroForm.onsubmit = (e) => {
        e.preventDefault();
        const badge = container.querySelector("#heroBadgeInput").value;
        const title = container.querySelector("#heroTitleInput").value;
        const subtitle = container.querySelector("#heroSubheadInput").value;
        const bgImage = bgInput.value;

        storage.setHeroBanner({ badge, title, subtitle, bgImage });
        utils.showToast("Hero Promo Banner updated! Check the storefront.", "success");
        this.render(container);
      };
    }

    // Catalog Events
    container.querySelectorAll(".admin-cat-filter").forEach(btn => {
      btn.onclick = () => {
        if (appContainer) appContainer.dataset.catalogFilter = btn.dataset.filter;
        this.catalogPage = 1;
        this.render(container);
      };
    });

    const searchInput = container.querySelector("#adminCatalogSearchInput");
    if (searchInput) {
      // Focus restoration trick
      const focusEnd = () => {
        if (searchInput) {
          searchInput.focus();
          const len = searchInput.value.length;
          searchInput.setSelectionRange(len, len);
        }
      };
      
      searchInput.oninput = (e) => {
        this.catalogSearch = e.target.value;
        this.catalogPage = 1;
        // Debounced re-render: with 1,747 products a render per
        // keystroke is unusable; wait for a pause, then restore focus.
        clearTimeout(this.catalogSearchTimer);
        this.catalogSearchTimer = setTimeout(() => {
          this.render(container);
          const newSearch = document.getElementById("adminCatalogSearchInput");
          if (newSearch) {
            newSearch.focus();
            const l = newSearch.value.length;
            newSearch.setSelectionRange(l, l);
          }
        }, 250);
      };
    }
    
    const stockFilter = container.querySelector("#adminStockFilter");
    if (stockFilter) {
      stockFilter.onchange = (e) => {
        this.catalogStockFilter = e.target.value;
        this.catalogPage = 1;
        this.render(container);
      };
    }

    const prevBtn = container.querySelector("#prevCatPageBtn");
    if (prevBtn) {
      prevBtn.onclick = () => {
        if (this.catalogPage > 1) {
          this.catalogPage--;
          this.render(container);
        }
      };
    }

    const nextBtn = container.querySelector("#nextCatPageBtn");
    if (nextBtn) {
      nextBtn.onclick = () => {
        this.catalogPage++;
        this.render(container);
      };
    }

    const exportCatBtn = container.querySelector("#exportCatalogBtn");
    if (exportCatBtn) {
      exportCatBtn.onclick = () => {
        const json = JSON.stringify(db.getProducts(), null, 2);
        const blob = new Blob([json], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `products_export_${Date.now()}.json`;
        a.click();
        utils.showToast("Catalog exported as JSON", "success");
      };
    }

    const resetCatBtn = container.querySelector("#resetCatalogBtn");
    if (resetCatBtn) {
      resetCatBtn.onclick = async () => {
        if (!confirm("Reset the catalogue to the original data/products.json? This discards saved product edits in this browser and reloads the page. Saved order/review changes in this browser are also lost on the next load, because clearing the catalogue cache makes the next load re-fetch all data files.")) return;
        try {
          const res = await fetch("data/products.json");
          if (!res.ok) throw new Error("HTTP " + res.status);
          const fresh = await res.json();
          if (!Array.isArray(fresh)) throw new Error("products.json is not a list");
          db.products = fresh;
          try { localStorage.removeItem("hrz_db_products_v31"); } catch {}
          utils.showToast("Original catalogue restored — reloading…", "success");
          setTimeout(() => window.location.reload(), 600);
        } catch (err) {
          console.error("Catalogue reset failed:", err);
          utils.showToast("Could not reload the original catalogue. Your edits were not changed.", "error");
        }
      };
    }

    const addProdBtn = container.querySelector("#addNewProductBtn");
    if (addProdBtn) {
      addProdBtn.onclick = () => this.openAddProductModal(container);
    }

    container.querySelectorAll(".edit-prod-btn").forEach(btn => {
      btn.onclick = () => this.openEditProductModal(container, btn.dataset.id);
    });

    container.querySelectorAll(".admin-quickedit-btn").forEach(btn => {
      btn.onclick = () => {
        this.editingProductId = btn.dataset.id;
        this.savedProductId = null;
        this.render(container);
        const priceInput = container.querySelector(`[data-edit-price="${btn.dataset.id}"]`);
        if (priceInput) priceInput.focus();
      };
    });

    container.querySelectorAll(".admin-cancel-btn").forEach(btn => {
      btn.onclick = () => {
        this.editingProductId = null;
        this.render(container);
      };
    });

    container.querySelectorAll(".admin-save-btn").forEach(btn => {
      btn.onclick = () => {
        const id = btn.dataset.id;
        const product = db.getProductById(id);
        const priceInput = container.querySelector(`[data-edit-price="${id}"]`);
        const stockSelect = container.querySelector(`[data-edit-stock="${id}"]`);
        if (!product) { utils.showToast("Product not found.", "error"); return; }
        const check = this._validateProductEdit(product.name, priceInput ? priceInput.value : "");
        if (!check.ok) { utils.showToast(check.error, "error"); return; }
        const inStock = stockSelect ? stockSelect.value === "true" : product.inStock;
        db.updateProduct(id, { price: check.price, inStock });
        this._clearUnsavedBannerIfPersisted();
        this.editingProductId = null;
        this.savedProductId = id;
        utils.showToast(`✓ Saved: ${product.name} — ${inStock ? "In Stock" : "Out of Stock"} at ${utils.formatCurrency(check.price)}`, "success");
        this.render(container);
      };
    });

    container.querySelectorAll(".delete-prod-btn").forEach(btn => {
      btn.onclick = () => {
        if (confirm("Are you sure you want to delete this product?")) {
          db.deleteProduct(btn.dataset.id);
          utils.showToast("Product deleted", "info");
          this.render(container);
        }
      };
    });

    // Fitment Rules
    container.querySelectorAll(".delete-comp-btn").forEach(btn => {
      btn.onclick = () => {
        db.deleteCompatibilityRule(btn.dataset.id);
        utils.showToast("Compatibility rule deleted", "info");
        this.render(container);
      };
    });

    const addCompBtn = container.querySelector("#addCompRuleBtn");
    if (addCompBtn) addCompBtn.onclick = () => this.openAddCompModal(container);

    // Reviews
    container.querySelectorAll(".approve-rev-btn").forEach(btn => {
      btn.onclick = () => {
        db.updateReviewStatus(btn.dataset.id, "published");
        utils.showToast("Review approved and published", "success");
        this.render(container);
      };
    });
    container.querySelectorAll(".reject-rev-btn").forEach(btn => {
      btn.onclick = () => {
        db.updateReviewStatus(btn.dataset.id, "rejected");
        utils.showToast("Review rejected", "info");
        this.render(container);
      };
    });

    // Orders
    container.querySelectorAll(".order-status-select").forEach(sel => {
      sel.onchange = () => {
        // Persist through the DB path (DB._persist); the tracking
        // page reads the same DB orders, so it shows the new status.
        // No order is invented here — only existing orders are updated.
        db.updateOrderStatus(sel.dataset.id, sel.value);
        this.savedOrderId = sel.dataset.id;
        const badge = sel.parentElement.querySelector(".admin-saved-badge");
        if (badge) badge.textContent = "✓ Saved";
        utils.showToast(`✓ Saved: order ${sel.dataset.id} is now “${sel.value}”`, "success");
      };
    });

    const orderSearchInput = container.querySelector("#adminOrderSearchInput");
    if (orderSearchInput) {
      orderSearchInput.oninput = (e) => {
        this.orderSearch = e.target.value;
        this.render(container);
        setTimeout(() => {
          const again = document.getElementById("adminOrderSearchInput");
          if (again) { again.focus(); const l = again.value.length; again.setSelectionRange(l, l); }
        }, 0);
      };
    }

    // CSV
    const exportBtn = container.querySelector("#exportCsvBtn");
    if (exportBtn) {
      exportBtn.onclick = () => {
        const csv = db.exportCompatibilityCSV();
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `HRz_Compatibility_Matrix_${Date.now()}.csv`;
        a.click();
        utils.showToast("CSV exported successfully", "success");
      };
    }

    const importInput = container.querySelector("#importCsvInput");
    if (importInput) {
      importInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (evt) => {
            const count = db.importCompatibilityCSV(evt.target.result);
            utils.showToast(`Successfully imported ${count} fitment rules`, "success");
            this.render(container);
          };
          reader.readAsText(file);
        }
      };
    }
  }

  static openAddProductModal(container) {
    let modal = document.getElementById("adminProductModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "adminProductModal";
      modal.className = "modal-overlay";
      document.body.appendChild(modal);
    }

    const categories = window.HRz.DB.getCategories();
    const escapeHTML = window.HRz.Utils.escapeHTML;

    modal.innerHTML = `
      <div class="modal-card" style="max-width: 820px; width: 95%;">
        <div class="modal-header">
          <div>
            <p class="eyebrow red" style="margin:0 0 4px 0; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Admin Catalog Manager</p>
            <h3 style="margin:0; font-size:20px;">Add New Product to Catalog</h3>
          </div>
          <button type="button" class="close-btn" id="closeAdminProdModal">✕</button>
        </div>
        <div class="modal-body" style="max-height:78vh; overflow-y:auto; padding:24px;">
          <form id="adminAddProdForm" class="admin-form-grid">
            <div class="form-group admin-form-full">
              <label>Product Name *</label>
              <input type="text" id="newProdName" required placeholder="e.g. Axor Apex Turbine Helmet" />
            </div>

            <div class="form-group">
              <label>Brand / Manufacturer</label>
              <input type="text" id="newProdBrand" placeholder="e.g. Axor, Cramster, SMK, Raida" />
            </div>

            <div class="form-group">
              <label>Category *</label>
              <select id="newProdCat" required>
                ${categories.map(c => `<option value="${escapeHTML(c)}">${escapeHTML(c)}</option>`).join("")}
                <option value="__CUSTOM__">+ Create Custom Category...</option>
              </select>
              <input type="text" id="customCatInput" placeholder="Enter Custom Category Name" style="display:none; margin-top:6px; background:#1c1e22; border:1px solid #333; color:#fff; padding:12px; border-radius:6px; width:100%;" />
            </div>

            <div class="form-group">
              <label>Subcategory</label>
              <input type="text" id="newProdSubcat" placeholder="e.g. Full Face, Riding Jackets, Touring" />
            </div>

            <div class="form-group">
              <label>SKU Code</label>
              <input type="text" id="newProdSku" placeholder="e.g. HRZ-AX-001" />
            </div>

            <div class="form-group">
              <label>Selling Price (INR) *</label>
              <input type="number" id="newProdPrice" required placeholder="3999" />
            </div>

            <div class="form-group">
              <label>Original / MRP Price (INR)</label>
              <input type="number" id="newProdOrigPrice" placeholder="4999" />
            </div>

            <div class="form-group">
              <label>In Stock</label>
              <select id="newProdInStock">
                <option value="true" selected>Yes (In Stock)</option>
                <option value="false">No (Out of Stock)</option>
              </select>
            </div>

            <div class="form-group">
              <label>Visible on Store</label>
              <select id="newProdIsVisible">
                <option value="true" selected>Yes (Visible to Riders)</option>
                <option value="false">No (Hidden from Storefront)</option>
              </select>
            </div>

            <div class="form-group">
              <label>Badge / Tag</label>
              <input type="text" id="newProdBadge" placeholder="e.g. BESTSELLER, OEM GRADE, NEW" />
            </div>

            <div class="form-group">
              <label>Authenticity Guarantee</label>
              <input type="text" id="newProdAuth" value="100% OEM Certified" />
            </div>

            <div class="form-group">
              <label>Warranty Terms</label>
              <input type="text" id="newProdWarranty" value="12 Months Warranty" />
            </div>

            <!-- Size Checkbox Grid Section -->
            <div class="form-group admin-form-full" style="background:#121316; padding:16px; border-radius:8px; border:1px solid #282a30;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <label style="font-weight:700; color:#fff; font-size:14px; margin:0;">Product Sizes (Check all sizes currently in stock)</label>
                <button type="button" class="small-action-btn" id="newProdSelectStdSizes" style="font-size:11px; padding:3px 8px;">Select M, L, XL</button>
              </div>
              <p style="font-size:12px; color:var(--mute); margin:0 0 12px 0;">Checked sizes will show as active selectable buttons on the store. Unchecked standard sizes will display struck-through and unselectable.</p>
              
              <div style="margin-bottom:12px;">
                <small style="color:#aaa; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Standard Apparel & Helmet Sizes</small>
                <div class="admin-sizes-checkbox-grid">
                  ${['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL'].map(s => `
                    <label class="admin-size-checkbox-item">
                      <input type="checkbox" name="newProdSize" value="${s}" ${['M', 'L', 'XL'].includes(s) ? 'checked' : ''} />
                      <span>${s}</span>
                    </label>
                  `).join("")}
                </div>
              </div>

              <div style="margin-bottom:12px;">
                <small style="color:#aaa; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Pants / Waist Sizes</small>
                <div class="admin-sizes-checkbox-grid">
                  ${['28', '30', '32', '34', '36', '38', '40', '42'].map(s => `
                    <label class="admin-size-checkbox-item">
                      <input type="checkbox" name="newProdSize" value="${s}" />
                      <span>${s}</span>
                    </label>
                  `).join("")}
                </div>
              </div>

              <div style="margin-bottom:12px;">
                <small style="color:#aaa; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Boots & Footwear Sizes</small>
                <div class="admin-sizes-checkbox-grid">
                  ${['UK 6', 'UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11', 'UK 12'].map(s => `
                    <label class="admin-size-checkbox-item">
                      <input type="checkbox" name="newProdSize" value="${s}" />
                      <span>${s}</span>
                    </label>
                  `).join("")}
                </div>
              </div>

              <div style="margin-top:8px;">
                <label style="font-size:12px; color:#aaa;">Custom / Additional Sizes (comma-separated, optional)</label>
                <input type="text" id="newProdCustomSizes" placeholder="e.g. Free Size, Universal" style="margin-top:4px;" />
              </div>
            </div>

            <div class="form-group admin-form-full">
              <label>Full Product Description</label>
              <textarea id="newProdDesc" rows="4" placeholder="Enter detailed product description..."></textarea>
            </div>

            <div class="form-group admin-form-full">
              <label>Key Features & Specifications (one per line)</label>
              <textarea id="newProdHighlights" rows="3" placeholder="CE Level 2 Certified Armor&#10;Aerodynamic Multi-density EPS&#10;Quick Release Micro-metric Buckle"></textarea>
            </div>

            <div class="form-group admin-form-full">
              <label>Product Image URL *</label>
              <input type="text" id="newProdImgUrl" value="images/crash_guard_product.webp" required placeholder="Image Path or URL" />
              
              <div style="margin-top:10px;">
                <label for="prodImgFileUpload" class="small-action-btn" style="display:inline-block; cursor:pointer;">📤 Upload Image File</label>
                <input type="file" id="prodImgFileUpload" accept="image/*" style="display:none;" />
              </div>
            </div>

            <div class="form-group admin-form-full">
              <label>Additional Gallery Images (one URL or path per line)</label>
              <textarea id="newProdGallery" rows="3" placeholder="images/sample_angle2.webp&#10;images/sample_angle3.webp"></textarea>
            </div>

            <div class="admin-form-full" style="margin-top: 16px; display:flex; gap:12px; justify-content:flex-end;">
              <button type="button" class="small-action-btn" id="cancelAddProdBtn">Cancel</button>
              <button type="submit" class="accent-button" style="min-width:180px;">Save & Publish Product</button>
            </div>
          </form>
        </div>
      </div>
    `;

    modal.classList.add("show");
    window.HRz.Utils.setupModalAccessibility(modal, () => modal.classList.remove("show"));
    document.getElementById("closeAdminProdModal").onclick = () => modal.classList.remove("show");
    const cancelAddBtn = document.getElementById("cancelAddProdBtn");
    if (cancelAddBtn) cancelAddBtn.onclick = () => modal.classList.remove("show");

    const selectStdBtn = document.getElementById("newProdSelectStdSizes");
    if (selectStdBtn) {
      selectStdBtn.onclick = () => {
        modal.querySelectorAll("input[name='newProdSize']").forEach(cb => {
          cb.checked = ['M', 'L', 'XL'].includes(cb.value);
        });
      };
    }

    const catSel = document.getElementById("newProdCat");
    const customCatInput = document.getElementById("customCatInput");
    catSel.onchange = () => {
      if (catSel.value === "__CUSTOM__") {
        customCatInput.style.display = "block";
        customCatInput.required = true;
      } else {
        customCatInput.style.display = "none";
        customCatInput.required = false;
      }
    };

    const fileInput = document.getElementById("prodImgFileUpload");
    const imgUrlInput = document.getElementById("newProdImgUrl");
    if (fileInput) {
      fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (evt) => { imgUrlInput.value = evt.target.result; };
          reader.readAsDataURL(file);
        }
      };
    }

    document.getElementById("adminAddProdForm").onsubmit = (e) => {
      e.preventDefault();
      const name = document.getElementById("newProdName").value.trim();
      let category = catSel.value;
      if (category === "__CUSTOM__") category = customCatInput.value.trim() || "General";
      const checked = AdminCMS._validateProductEdit(name, document.getElementById("newProdPrice").value);
      if (!checked.ok) { window.HRz.Utils.showToast(checked.error, "error"); return; }
      const price = checked.price;
      const origRaw = parseFloat(document.getElementById("newProdOrigPrice").value);
      const originalPrice = (Number.isFinite(origRaw) && origRaw >= 0) ? origRaw : price;
      const brand = document.getElementById("newProdBrand").value.trim();
      const subcategory = document.getElementById("newProdSubcat").value.trim();
      const sku = document.getElementById("newProdSku").value.trim();
      const badge = document.getElementById("newProdBadge").value.trim();
      const authenticity = document.getElementById("newProdAuth").value.trim();
      const warranty = document.getElementById("newProdWarranty").value.trim();
      const description = document.getElementById("newProdDesc").value.trim();
      const inStock = document.getElementById("newProdInStock").value === "true";
      const isVisible = document.getElementById("newProdIsVisible").value === "true";
      const image = imgUrlInput.value || "images/crash_guard_product.webp";

      const checkedSizes = Array.from(modal.querySelectorAll("input[name='newProdSize']:checked")).map(cb => cb.value);
      const customSizesStr = document.getElementById("newProdCustomSizes").value.trim();
      const customSizes = customSizesStr ? customSizesStr.split(",").map(s => s.trim().toUpperCase()).filter(Boolean) : [];
      const availableSizes = Array.from(new Set([...checkedSizes, ...customSizes]));

      const APPAREL_SIZES = ['S', 'M', 'L', 'XL', '2XL', '3XL'];
      const PANTS_SIZES = ['30', '32', '34', '36', '38', '40'];
      const BOOTS_SIZES = ['UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11', 'UK 12'];

      let allSizes = [];
      if (category === 'Riding Pants' || checkedSizes.some(s => PANTS_SIZES.includes(s))) {
        allSizes = Array.from(new Set([...PANTS_SIZES, ...availableSizes]));
      } else if (category === 'Boots & Footwear' || checkedSizes.some(s => s.startsWith('UK'))) {
        allSizes = Array.from(new Set([...BOOTS_SIZES, ...availableSizes]));
      } else if (checkedSizes.length > 0 || ['Riding Jackets & Apparel', 'Helmets', 'Gloves'].includes(category)) {
        allSizes = Array.from(new Set([...APPAREL_SIZES, ...availableSizes]));
      } else {
        allSizes = [...availableSizes];
      }
      const sizes = availableSizes.join(", ");

      const highlights = document.getElementById("newProdHighlights").value
        .split('\n')
        .map(h => h.trim())
        .filter(Boolean);

      const galleryLines = document.getElementById("newProdGallery").value
        .split('\n')
        .map(g => g.trim())
        .filter(Boolean);
      const gallery = [image, ...galleryLines.filter(g => g !== image)];

      const newProduct = window.HRz.DB.addProduct({
        name, brand, category, subcategory, price, originalPrice, sku,
        badge, authenticity, warranty, description, inStock, isVisible,
        image, gallery, availableSizes, allSizes, sizes, highlights
      });

      // Direct Server Sync
      fetch('/api/update-product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: newProduct.id, updates: newProduct })
      }).catch(err => console.warn('Server sync error:', err));

      modal.classList.remove("show");
      window.HRz.Utils.showToast(`Product "${name}" added to catalog & saved!`, "success");
      this.render(container);
    };
  }

  static openEditProductModal(container, productId) {
    const product = window.HRz.DB.getProductById(productId);
    if (!product) return;

    let modal = document.getElementById("adminProductModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "adminProductModal";
      modal.className = "modal-overlay";
      document.body.appendChild(modal);
    }

    const categories = window.HRz.DB.getCategories();
    const escapeHTML = window.HRz.Utils.escapeHTML;

    // Collect current available sizes
    let currentAvailSizes = [];
    if (Array.isArray(product.availableSizes) && product.availableSizes.length > 0) {
      currentAvailSizes = [...product.availableSizes];
    } else if (product.sizes) {
      currentAvailSizes = product.sizes.split(',').map(s => s.trim().toUpperCase()).filter(Boolean);
    }

    const highlightsText = (product.highlights || []).join('\n');
    const galleryText = (product.gallery || []).filter(img => img !== product.image).join('\n');

    const KNOWN_SIZES = [
      'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL',
      '28', '30', '32', '34', '36', '38', '40', '42',
      'UK 6', 'UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11', 'UK 12'
    ];
    const customSizes = currentAvailSizes.filter(s => !KNOWN_SIZES.includes(s));
    const customSizesText = customSizes.join(', ');

    modal.innerHTML = `
      <div class="modal-card" style="max-width: 820px; width: 95%;">
        <div class="modal-header">
          <div>
            <p class="eyebrow red" style="margin:0 0 4px 0; font-size:11px; text-transform:uppercase; letter-spacing:1px;">Admin Catalog Manager</p>
            <h3 style="margin:0; font-size:20px;">Edit Product: ${escapeHTML(product.name)}</h3>
          </div>
          <button type="button" class="close-btn" id="closeAdminProdModal">✕</button>
        </div>
        <div class="modal-body" style="max-height:78vh; overflow-y:auto; padding:24px;">
          <form id="adminEditProdForm" class="admin-form-grid">
            <div class="form-group admin-form-full">
              <label>Product Name *</label>
              <input type="text" id="editProdName" required value="${escapeHTML(product.name)}" />
            </div>

            <div class="form-group">
              <label>Brand / Manufacturer</label>
              <input type="text" id="editProdBrand" value="${escapeHTML(product.brand || '')}" placeholder="e.g. Axor, Cramster, SMK, Raida" />
            </div>

            <div class="form-group">
              <label>Primary Category *</label>
              <select id="editProdCat" required>
                ${categories.map(c => `<option value="${escapeHTML(c)}" ${product.category === c ? 'selected' : ''}>${escapeHTML(c)}</option>`).join("")}
                <option value="__CUSTOM__">+ Create Custom Category...</option>
              </select>
              <input type="text" id="editCustomCatInput" placeholder="Enter Custom Category Name" style="display:none; margin-top:6px; background:#1c1e22; border:1px solid #333; color:#fff; padding:12px; border-radius:6px; width:100%;" />
            </div>

            <div class="form-group">
              <label>Subcategory</label>
              <input type="text" id="editProdSubcat" value="${escapeHTML(product.subcategory || '')}" placeholder="e.g. Full Face Helmets, Touring Jackets" />
            </div>

            <div class="form-group">
              <label>SKU Code</label>
              <input type="text" id="editProdSku" value="${escapeHTML(product.sku || '')}" placeholder="e.g. HRZ-JKT-001" />
            </div>

            <div class="form-group">
              <label>Selling Price (INR) *</label>
              <input type="number" id="editProdPrice" required value="${product.price}" />
            </div>

            <div class="form-group">
              <label>Original / MRP Price (INR)</label>
              <input type="number" id="editProdOrigPrice" value="${product.originalPrice || ''}" placeholder="Optional strike-through MRP" />
            </div>

            <div class="form-group">
              <label>In Stock</label>
              <select id="editProdInStock">
                <option value="true" ${product.inStock ? 'selected' : ''}>Yes (In Stock)</option>
                <option value="false" ${!product.inStock ? 'selected' : ''}>No (Out of Stock)</option>
              </select>
            </div>

            <div class="form-group">
              <label>Visible on Store</label>
              <select id="editProdIsVisible">
                <option value="true" ${product.isVisible !== false ? 'selected' : ''}>Yes (Visible to Riders)</option>
                <option value="false" ${product.isVisible === false ? 'selected' : ''}>No (Hidden from Storefront)</option>
              </select>
            </div>

            <div class="form-group">
              <label>Badge / Tag</label>
              <input type="text" id="editProdBadge" value="${escapeHTML(product.badge || '')}" placeholder="e.g. BESTSELLER, OEM GRADE, NEW" />
            </div>

            <div class="form-group">
              <label>Authenticity Guarantee</label>
              <input type="text" id="editProdAuth" value="${escapeHTML(product.authenticity || '100% OEM Certified')}" placeholder="e.g. 100% OEM Certified" />
            </div>

            <div class="form-group">
              <label>Warranty Terms</label>
              <input type="text" id="editProdWarranty" value="${escapeHTML(product.warranty || '12 Months Warranty')}" placeholder="e.g. 12 Months Warranty" />
            </div>

            <!-- Size Selection Checkboxes Section -->
            <div class="form-group admin-form-full" style="background:#121316; padding:16px; border-radius:8px; border:1px solid #282a30;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <label style="font-weight:700; color:#fff; font-size:14px; margin:0;">Product Sizes (Check all sizes currently in stock)</label>
                <button type="button" class="small-action-btn" id="adminSelectAllSizesBtn" style="font-size:11px; padding:3px 8px;">Select Standard S–XL</button>
              </div>
              <p style="font-size:12px; color:var(--mute); margin:0 0 12px 0;">Checked sizes will show as active selectable buttons on the store. Unchecked standard sizes will display struck-through and unselectable.</p>
              
              <div style="margin-bottom:12px;">
                <small style="color:#aaa; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Standard Apparel & Helmet Sizes</small>
                <div class="admin-sizes-checkbox-grid">
                  ${['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL'].map(s => `
                    <label class="admin-size-checkbox-item">
                      <input type="checkbox" name="editProdSize" value="${s}" ${currentAvailSizes.includes(s) ? 'checked' : ''} />
                      <span>${s}</span>
                    </label>
                  `).join("")}
                </div>
              </div>

              <div style="margin-bottom:12px;">
                <small style="color:#aaa; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Pants / Waist Sizes</small>
                <div class="admin-sizes-checkbox-grid">
                  ${['28', '30', '32', '34', '36', '38', '40', '42'].map(s => `
                    <label class="admin-size-checkbox-item">
                      <input type="checkbox" name="editProdSize" value="${s}" ${currentAvailSizes.includes(s) ? 'checked' : ''} />
                      <span>${s}</span>
                    </label>
                  `).join("")}
                </div>
              </div>

              <div style="margin-bottom:12px;">
                <small style="color:#aaa; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Boots & Footwear Sizes</small>
                <div class="admin-sizes-checkbox-grid">
                  ${['UK 6', 'UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11', 'UK 12'].map(s => `
                    <label class="admin-size-checkbox-item">
                      <input type="checkbox" name="editProdSize" value="${s}" ${currentAvailSizes.includes(s) ? 'checked' : ''} />
                      <span>${s}</span>
                    </label>
                  `).join("")}
                </div>
              </div>

              <div style="margin-top:8px;">
                <label style="font-size:12px; color:#aaa;">Custom / Additional Sizes (comma-separated, optional)</label>
                <input type="text" id="adminCustomSizesInput" value="${escapeHTML(customSizesText)}" placeholder="e.g. Free Size, Universal" style="margin-top:4px;" />
              </div>
            </div>

            <div class="form-group admin-form-full">
              <label>Full Product Description</label>
              <textarea id="editProdDesc" rows="4" placeholder="Detailed product description...">${escapeHTML(product.description || '')}</textarea>
            </div>

            <div class="form-group admin-form-full">
              <label>Key Features & Specifications (one per line)</label>
              <textarea id="editProdHighlights" rows="3" placeholder="CE Level 2 Certified Armor&#10;Waterproof Breathable Membrane&#10;Reflective 3M Scotchlite Inserts">${escapeHTML(highlightsText)}</textarea>
            </div>

            <div class="form-group admin-form-full">
              <label>Primary Product Image URL *</label>
              <input type="text" id="editProdImgUrl" required value="${escapeHTML(product.image || '')}" />
              
              <div style="margin-top:10px;">
                <label for="editProdImgFileUpload" class="small-action-btn" style="display:inline-block; cursor:pointer;">📤 Upload Image File</label>
                <input type="file" id="editProdImgFileUpload" accept="image/*" style="display:none;" />
              </div>
            </div>

            <div class="form-group admin-form-full">
              <label>Additional Gallery Images (one URL or path per line)</label>
              <textarea id="editProdGallery" rows="3" placeholder="images/sample_angle2.webp&#10;images/sample_angle3.webp">${escapeHTML(galleryText)}</textarea>
            </div>

            <div class="admin-form-full" style="margin-top: 16px; display:flex; gap:12px; justify-content:flex-end;">
              <button type="button" class="small-action-btn" id="cancelEditProdBtn">Cancel</button>
              <button type="submit" class="accent-button" style="min-width:180px;">Save Changes & Sync</button>
            </div>
          </form>
        </div>
      </div>
    `;

    modal.classList.add("show");
    window.HRz.Utils.setupModalAccessibility(modal, () => modal.classList.remove("show"));
    document.getElementById("closeAdminProdModal").onclick = () => modal.classList.remove("show");
    const cancelEditBtn = document.getElementById("cancelEditProdBtn");
    if (cancelEditBtn) cancelEditBtn.onclick = () => modal.classList.remove("show");

    const selectStdBtn = document.getElementById("adminSelectAllSizesBtn");
    if (selectStdBtn) {
      selectStdBtn.onclick = () => {
        modal.querySelectorAll("input[name='editProdSize']").forEach(cb => {
          cb.checked = ['S', 'M', 'L', 'XL'].includes(cb.value);
        });
      };
    }

    const catSel = document.getElementById("editProdCat");
    const customCatInput = document.getElementById("editCustomCatInput");
    catSel.onchange = () => {
      if (catSel.value === "__CUSTOM__") {
        customCatInput.style.display = "block";
        customCatInput.required = true;
      } else {
        customCatInput.style.display = "none";
        customCatInput.required = false;
      }
    };

    const fileInput = document.getElementById("editProdImgFileUpload");
    const imgUrlInput = document.getElementById("editProdImgUrl");
    if (fileInput) {
      fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (evt) => { imgUrlInput.value = evt.target.result; };
          reader.readAsDataURL(file);
        }
      };
    }

    document.getElementById("adminEditProdForm").onsubmit = (e) => {
      e.preventDefault();
      const name = document.getElementById("editProdName").value.trim();
      let category = catSel.value;
      if (category === "__CUSTOM__") category = customCatInput.value.trim() || "General";
      const checked = AdminCMS._validateProductEdit(name, document.getElementById("editProdPrice").value);
      if (!checked.ok) { window.HRz.Utils.showToast(checked.error, "error"); return; }
      const price = checked.price;
      const origRaw = parseFloat(document.getElementById("editProdOrigPrice").value);
      const originalPrice = (Number.isFinite(origRaw) && origRaw >= 0) ? origRaw : (product.originalPrice ?? price);
      const brand = document.getElementById("editProdBrand").value.trim();
      const subcategory = document.getElementById("editProdSubcat").value.trim();
      const sku = document.getElementById("editProdSku").value.trim() || product.sku;
      const badge = document.getElementById("editProdBadge").value.trim();
      const authenticity = document.getElementById("editProdAuth").value.trim();
      const warranty = document.getElementById("editProdWarranty").value.trim();
      const description = document.getElementById("editProdDesc").value.trim();
      const inStock = document.getElementById("editProdInStock").value === "true";
      const isVisible = document.getElementById("editProdIsVisible").value === "true";
      const image = imgUrlInput.value || product.image;

      // Collect checked sizes
      const checkedSizes = Array.from(modal.querySelectorAll("input[name='editProdSize']:checked")).map(cb => cb.value);
      const customSizesStr = document.getElementById("adminCustomSizesInput").value.trim();
      const customSizes = customSizesStr ? customSizesStr.split(",").map(s => s.trim().toUpperCase()).filter(Boolean) : [];
      const availableSizes = Array.from(new Set([...checkedSizes, ...customSizes]));

      // Determine allSizes
      const APPAREL_SIZES = ['S', 'M', 'L', 'XL', '2XL', '3XL'];
      const PANTS_SIZES = ['30', '32', '34', '36', '38', '40'];
      const BOOTS_SIZES = ['UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11', 'UK 12'];

      let allSizes = [];
      if (category === 'Riding Pants' || checkedSizes.some(s => PANTS_SIZES.includes(s))) {
        allSizes = Array.from(new Set([...PANTS_SIZES, ...availableSizes]));
      } else if (category === 'Boots & Footwear' || checkedSizes.some(s => s.startsWith('UK'))) {
        allSizes = Array.from(new Set([...BOOTS_SIZES, ...availableSizes]));
      } else if (checkedSizes.length > 0 || ['Riding Jackets & Apparel', 'Helmets', 'Gloves'].includes(category)) {
        allSizes = Array.from(new Set([...APPAREL_SIZES, ...availableSizes]));
      } else {
        allSizes = [...availableSizes];
      }
      const sizes = availableSizes.join(", ");

      const highlights = document.getElementById("editProdHighlights").value
        .split('\n')
        .map(h => h.trim())
        .filter(Boolean);

      const galleryLines = document.getElementById("editProdGallery").value
        .split('\n')
        .map(g => g.trim())
        .filter(Boolean);
      const gallery = [image, ...galleryLines.filter(g => g !== image)];

      const updates = {
        name, brand, category, subcategory, price, originalPrice, sku,
        badge, authenticity, warranty, description, inStock, isVisible,
        image, gallery, availableSizes, allSizes, sizes, highlights
      };

      window.HRz.DB.updateProduct(productId, updates);
      AdminCMS._clearUnsavedBannerIfPersisted();
      AdminCMS.savedProductId = productId;

      // Direct Server Sync
      fetch('/api/update-product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: productId, updates })
      }).catch(err => console.warn('Server sync error:', err));

      modal.classList.remove("show");
      window.HRz.Utils.showToast(`Product "${name}" updated & saved!`, "success");
      this.render(container);
    };
  }

  static openAddCompModal(container) {
    let modal = document.getElementById("adminCompModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "adminCompModal";
      modal.className = "modal-overlay";
      document.body.appendChild(modal);
    }

    const prods = window.HRz.DB.getProducts();
    const bikes = window.HRz.DB.getBikes();
    const escapeHTML = window.HRz.Utils.escapeHTML;

    modal.innerHTML = `
      <div class="modal-card">
        <div class="modal-header">
          <h3>Create Fitment Compatibility Link</h3>
          <button type="button" class="close-btn" id="closeAdminCompModal">✕</button>
        </div>
        <div class="modal-body">
          <form id="adminAddCompForm" class="admin-form-grid">
            <div class="form-group admin-form-full">
              <label>Select Product *</label>
              <select id="compSelectProduct" required>
                ${prods.map(p => `<option value="${escapeHTML(p.id)}">${escapeHTML(p.name)} (${escapeHTML(p.sku)})</option>`).join("")}
              </select>
            </div>
            <div class="form-group admin-form-full">
              <label>Select Motorcycle *</label>
              <select id="compSelectBike" required>
                ${bikes.map(b => `<option value="${escapeHTML(b.id)}">${escapeHTML(b.brand)} ${escapeHTML(b.model)} (${escapeHTML(b.variant)})</option>`).join("")}
              </select>
            </div>
            <div class="form-group admin-form-full">
              <label>Fit Type *</label>
              <select id="compFitType" required>
                <option value="OEM Fit">OEM Fit (Direct Mount)</option>
                <option value="Universal Fit">Universal Fit</option>
                <option value="Requires Adapter">Requires Adapter Bracket</option>
              </select>
            </div>
            <div class="form-group admin-form-full">
              <label>Fitment Notes</label>
              <input type="text" id="compNotes" placeholder="e.g. Mounts using stock chassis bolts" />
            </div>
            <div class="admin-form-full" style="margin-top:16px;">
              <button type="submit" class="accent-button full-width-btn">Link Compatibility</button>
            </div>
          </form>
        </div>
      </div>
    `;

    modal.classList.add("show");
    window.HRz.Utils.setupModalAccessibility(modal, () => modal.classList.remove("show"));
    document.getElementById("closeAdminCompModal").onclick = () => modal.classList.remove("show");

    document.getElementById("adminAddCompForm").onsubmit = (e) => {
      e.preventDefault();
      const pId = document.getElementById("compSelectProduct").value;
      const bId = document.getElementById("compSelectBike").value;
      const fitType = document.getElementById("compFitType").value;
      const notes = document.getElementById("compNotes").value;

      window.HRz.DB.addCompatibilityRule(pId, bId, fitType, notes);
      modal.classList.remove("show");
      window.HRz.Utils.showToast("Compatibility rule linked", "success");
      this.render(container);
    };
  }
}

window.HRz.Admin = AdminCMS;

