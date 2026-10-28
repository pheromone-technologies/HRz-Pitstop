"""
Restore js/catalog.js to the user's authentic live UI design from hrzpitstop.vercel.app
as shown in the user's screenshot, with full slide-out filter drawer, [FILTER & SORT] button,
4-column card grid with red category and + BAG button, and flexible category matching.
"""

catalog_js_code = r'''/* =============================================
   HRz PITSTOP – Product Catalog & Filtering Module
   Adapted for Premium Slide-out Drawer Filtering
   ============================================= */

window.HRz = window.HRz || {};

class CatalogView {
  static activeCategory = "All";
  static activeSubcategory = "All";
  static searchQuery = "";
  static sortBy = "featured";
  static activeBrands = new Set();
  static activeColors = new Set();
  static activeSubtypes = new Set();
  static minPrice = null;
  static maxPrice = null;

  static BASE_COLORS = [
    { name: "Black", hex: "#222222" },
    { name: "White", hex: "#FFFFFF" },
    { name: "Red", hex: "#E53935" },
    { name: "Blue", hex: "#1E88E5" },
    { name: "Green", hex: "#43A047" },
    { name: "Yellow", hex: "#FDD835" },
    { name: "Orange", hex: "#FB8C00" },
    { name: "Grey", hex: "#757575" },
    { name: "Silver", hex: "#BDBDBD" },
    { name: "Neon", hex: "#76FF03" }
  ];

  static render(container, options = {}) {
    if (options.category !== undefined) {
      if (this.activeCategory !== options.category) {
        this.activeCategory = options.category;
        this.resetAdvancedFilters();
      }
    }
    if (options.subcategory !== undefined) {
      this.activeSubcategory = options.subcategory;
    } else {
      this.activeSubcategory = "All";
    }
    if (options.search !== undefined) {
      if (this.searchQuery !== options.search) {
        this.searchQuery = options.search;
        this.resetAdvancedFilters();
      }
    }

    const activeBike = window.HRz.Storage.getActiveBike();
    const wishlist = window.HRz.Storage.getWishlist();
    const escapeHTML = window.HRz.Utils.escapeHTML;

    let allBaseProducts = window.HRz.DB.products || [];
    let products = [...allBaseProducts];

    if (this.searchQuery) {
      products = window.HRz.Utils.smartSearch(this.searchQuery, products, null);
    }

    if (this.activeCategory && this.activeCategory !== "All") {
      const targetCat = this.activeCategory.toLowerCase().trim();
      products = products.filter(p => {
        const pCat = (p.category || "").toLowerCase().trim();
        if (pCat === targetCat) return true;

        if (targetCat === "helmets" || targetCat === "helmet") {
          return pCat === "helmets";
        }
        if (targetCat === "riding gears" || targetCat === "riding gear" || targetCat === "gears" || targetCat === "jackets" || targetCat === "apparel") {
          return ["riding jackets & apparel", "gloves", "riding pants", "boots & footwear", "protective gear"].includes(pCat);
        }
        if (targetCat === "protection" || targetCat === "crash protection") {
          return pCat === "crash protection" || pCat.includes("protection");
        }
        if (targetCat === "luggage" || targetCat === "touring" || targetCat === "luggage & storage") {
          return pCat === "luggage & storage" || pCat.includes("luggage");
        }
        if (targetCat === "lights" || targetCat === "lighting" || targetCat === "lighting & electrical") {
          return pCat === "lighting & electrical" || pCat === "electronics";
        }
        if (targetCat === "maintenance" || targetCat === "oils") {
          return ["engine oils & lubricants", "maintenance & cleaning", "tools & workshop equipment"].includes(pCat);
        }
        if (targetCat === "performance" || targetCat === "performance parts") {
          return ["performance parts", "exhaust system", "drive & transmission", "braking components", "suspension components", "engine components", "cables & controls", "body parts & panels", "mirrors & handlebar accessories", "tyres & wheels"].includes(pCat);
        }
        return pCat.includes(targetCat);
      });
    }

    if (this.activeSubcategory && this.activeSubcategory !== "All") {
      const targetSub = this.activeSubcategory.toLowerCase().trim();
      products = products.filter(p => {
        const pSub = (p.subcategory || "").toLowerCase().trim();
        const pName = (p.name || "").toLowerCase();
        return pSub === targetSub || pName.includes(targetSub);
      });
    }

    const availableBrands = [...new Set(products.map(p => p.brand).filter(Boolean))].sort();

    const availableBaseColors = new Set();
    products.forEach(p => {
      if (p.variants) {
        p.variants.forEach(v => {
          const vColor = (v.color || "").toLowerCase();
          this.BASE_COLORS.forEach(bc => {
            if (vColor.includes(bc.name.toLowerCase())) availableBaseColors.add(bc.name);
          });
        });
      }
    });

    const availableSubtypes = new Set();
    let subtypeLabel = "";
    const activeCatLower = (this.activeCategory || "").toLowerCase();
    if (activeCatLower === "helmets") {
      subtypeLabel = "Helmet Type";
      products.forEach(p => {
        const n = p.name.toLowerCase();
        if (n.includes('full face') || n.includes('full-face')) availableSubtypes.add("Full Face");
        else if (n.includes('half face') || n.includes('open face')) availableSubtypes.add("Half Face");
        else if (n.includes('offroad') || n.includes('motocross') || n.includes('dirt')) availableSubtypes.add("Offroad");
        else if (n.includes('modular')) availableSubtypes.add("Modular");
      });
    } else if (activeCatLower.includes("luggage")) {
      subtypeLabel = "Luggage Type";
      products.forEach(p => {
        const n = p.name.toLowerCase();
        if (n.includes('saddle')) availableSubtypes.add("Saddlebags");
        else if (n.includes('tank')) availableSubtypes.add("Tank Bags");
        else if (n.includes('tail')) availableSubtypes.add("Tail Bags");
        else if (n.includes('top case') || n.includes('box')) availableSubtypes.add("Top Cases");
        else if (n.includes('backpack')) availableSubtypes.add("Backpacks");
      });
    } else if (activeCatLower.includes("protection")) {
      subtypeLabel = "Protection Type";
      products.forEach(p => {
        const n = p.name.toLowerCase();
        if (n.includes('crash guard') || n.includes('engine guard')) availableSubtypes.add("Crash Guards");
        else if (n.includes('bash plate') || n.includes('skid plate')) availableSubtypes.add("Bash Plates");
        else if (n.includes('slider')) availableSubtypes.add("Sliders");
        else if (n.includes('radiator')) availableSubtypes.add("Radiator Guards");
      });
    } else if (activeCatLower.includes("gear") || activeCatLower.includes("riding")) {
      subtypeLabel = "Apparel Type";
      products.forEach(p => {
        const n = p.name.toLowerCase();
        if (n.includes('jacket')) availableSubtypes.add("Jackets");
        else if (n.includes('glove')) availableSubtypes.add("Gloves");
        else if (n.includes('pant') || n.includes('trouser')) availableSubtypes.add("Pants");
        else if (n.includes('shoe') || n.includes('boot')) availableSubtypes.add("Footwear");
      });
    }

    if (this.activeBrands.size > 0) {
      products = products.filter(p => this.activeBrands.has(p.brand));
    }
    if (this.activeColors.size > 0) {
      products = products.filter(p => {
        if (!p.variants) return false;
        return p.variants.some(v => {
          const vCol = (v.color || "").toLowerCase();
          for (const ac of this.activeColors) {
            if (vCol.includes(ac.toLowerCase())) return true;
          }
          return false;
        });
      });
    }
    if (this.activeSubtypes.size > 0) {
      products = products.filter(p => {
        const n = p.name.toLowerCase();
        for (const st of this.activeSubtypes) {
          const stLower = st.toLowerCase().replace(/s$/, '');
          if (n.includes(stLower)) return true;
        }
        return false;
      });
    }

    if (this.minPrice !== null) products = products.filter(p => p.price >= this.minPrice);
    if (this.maxPrice !== null) products = products.filter(p => p.price <= this.maxPrice);

    if (this.sortBy === "price-low") products.sort((a, b) => a.price - b.price);
    else if (this.sortBy === "price-high") products.sort((a, b) => b.price - a.price);
    else if (this.sortBy === "rating") products.sort((a, b) => b.rating - a.rating);

    const pageTitle = this.activeCategory !== "All" ? this.activeCategory.toUpperCase() : "PRODUCT CATALOG";
    const eyebrowText = this.activeCategory !== "All" ? `Explore Premium ${this.activeCategory}` : "Guaranteed Motorcycle Parts";

    let activeFilterCount = this.activeBrands.size + this.activeColors.size + this.activeSubtypes.size + (this.minPrice ? 1 : 0) + (this.maxPrice ? 1 : 0);

    container.innerHTML = `
      <div class="breadcrumb-trail">
        <a href="#home">Home</a> / <span class="current">${escapeHTML(this.activeCategory === "All" ? "Shop All" : this.activeCategory)}</span>
      </div>

      <div class="view-header">
        <div>
          <p class="eyebrow red">${escapeHTML(eyebrowText)}</p>
          <h2>${escapeHTML(pageTitle)}</h2>
        </div>
      </div>

      <div class="catalog-container inner-section" style="padding-top: 10px;">
        <div class="view-header" style="padding: 0; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px;">
           <button class="open-filter-btn" id="openFilterDrawerBtn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
              Filter & Sort ${activeFilterCount > 0 ? `<span class="filter-count-badge">${activeFilterCount}</span>` : ''}
           </button>
           <p style="color: #888; font-size: 13px; margin:0;">Showing ${products.length} products</p>
        </div>

        ${products.length === 0 ? `
          <div class="empty-state-card" style="margin: 0; max-width: 100%;">
            <div class="empty-icon">🔍</div>
            <h3>No Parts Found</h3>
            <p>We couldn't find any products matching your selected filters.</p>
            <button class="accent-button" id="resetCatalogFiltersBtnMain">Reset Filters</button>
          </div>
        ` : `
          <div class="product-grid" id="catalogProductGrid">
            ${this.renderSkeletons(Math.min(products.length, 8))}
          </div>
        `}

        <aside class="filter-drawer" id="catalogFilterDrawer">
          <div class="filter-drawer-head">
            <h3>Filter ${this.activeCategory !== "All" ? this.activeCategory : "Products"}</h3>
            <button class="close-filter-btn" id="closeFilterDrawerBtn">×</button>
          </div>
          <div class="filter-drawer-body">

            <div class="filter-group">
              <div class="filter-group-header">
                <h4>Sort By</h4>
              </div>
              <div class="filter-options">
                <select id="catalogSortSelectDrawer" class="premium-select">
                  <option value="featured" ${this.sortBy === "featured" ? "selected" : ""}>Featured</option>
                  <option value="price-low" ${this.sortBy === "price-low" ? "selected" : ""}>Price: Low to High</option>
                  <option value="price-high" ${this.sortBy === "price-high" ? "selected" : ""}>Price: High to Low</option>
                  <option value="rating" ${this.sortBy === "rating" ? "selected" : ""}>Customer Rating</option>
                </select>
              </div>
            </div>

            ${this.activeCategory === "All" ? `
            <div class="filter-group">
              <div class="filter-group-header">
                <h4>Category</h4>
              </div>
              <div class="filter-pill-grid">
                ${(window.HRz.DB.getCategories ? window.HRz.DB.getCategories() : []).map(cat => `
                  <label class="premium-filter-pill">
                    <input type="radio" name="cat_filter" value="${escapeHTML(cat)}">
                    <span>${escapeHTML(cat)}</span>
                  </label>
                `).join('')}
              </div>
            </div>
            ` : ''}

            ${availableSubtypes.size > 0 ? `
            <div class="filter-group">
              <div class="filter-group-header">
                <h4>${escapeHTML(subtypeLabel)}</h4>
              </div>
              <div class="filter-pill-grid">
                ${[...availableSubtypes].sort().map(st => `
                  <label class="premium-filter-pill">
                    <input type="checkbox" class="subtype-filter-cb" value="${escapeHTML(st)}" ${this.activeSubtypes.has(st) ? 'checked' : ''}>
                    <span>${escapeHTML(st)}</span>
                  </label>
                `).join('')}
              </div>
            </div>
            ` : ''}

            ${availableBrands.length > 0 ? `
            <div class="filter-group">
              <div class="filter-group-header">
                <h4>Brands</h4>
              </div>
              <div class="filter-pill-grid">
                ${availableBrands.map(b => `
                  <label class="premium-filter-pill">
                    <input type="checkbox" class="brand-filter-cb" value="${escapeHTML(b)}" ${this.activeBrands.has(b) ? 'checked' : ''}>
                    <span>${escapeHTML(b)}</span>
                  </label>
                `).join('')}
              </div>
            </div>
            ` : ''}

            ${availableBaseColors.size > 0 ? `
            <div class="filter-group">
              <div class="filter-group-header">
                <h4>Colors</h4>
              </div>
              <div class="color-swatch-grid">
                ${this.BASE_COLORS.filter(c => availableBaseColors.has(c.name)).map(c => `
                  <div class="color-swatch ${this.activeColors.has(c.name) ? 'selected' : ''}" data-color="${escapeHTML(c.name)}" style="background-color: ${c.hex};" title="${escapeHTML(c.name)}">
                    <span class="swatch-check">✓</span>
                  </div>
                `).join('')}
              </div>
            </div>
            ` : ''}

            <div class="filter-group">
              <div class="filter-group-header">
                <h4>Price Range (₹)</h4>
              </div>
              <div class="price-range-inputs premium-price-range">
                <input type="number" id="minPriceInput" placeholder="Min" value="${this.minPrice || ''}">
                <span class="range-divider">-</span>
                <input type="number" id="maxPriceInput" placeholder="Max" value="${this.maxPrice || ''}">
              </div>
            </div>

          </div>
          <div class="filter-drawer-footer">
            <button class="btn-outline" id="clearFiltersBtn">Clear</button>
            <button class="btn-primary" id="applyFiltersBtn">Show Results</button>
          </div>
        </aside>
      </div>
    `;

    this.bindDrawerEvents(container);

    const resetBtnMain = container.querySelector("#resetCatalogFiltersBtnMain");
    if (resetBtnMain) {
      resetBtnMain.onclick = () => {
        this.resetAdvancedFilters();
        this.render(container);
      };
    }

    const grid = container.querySelector("#catalogProductGrid");
    if (grid && products.length > 0) {
      setTimeout(() => {
        grid.innerHTML = products.map(p => this.renderProductCard(p, activeBike, wishlist)).join("");
        this.bindCardEvents(container);
      }, 150);
    }
  }

  static resetAdvancedFilters() {
    this.activeBrands.clear();
    this.activeColors.clear();
    this.activeSubtypes.clear();
    this.minPrice = null;
    this.maxPrice = null;
  }

  static bindDrawerEvents(container) {
    const drawer = container.querySelector("#catalogFilterDrawer");
    const overlay = document.getElementById("overlay");
    const openBtn = container.querySelector("#openFilterDrawerBtn");
    const closeBtn = container.querySelector("#closeFilterDrawerBtn");
    const clearBtn = container.querySelector("#clearFiltersBtn");
    const applyBtn = container.querySelector("#applyFiltersBtn");

    const closeDrawer = () => {
      drawer.classList.remove("open");
      if (overlay) overlay.classList.remove("open");
    };

    if (openBtn) {
      openBtn.onclick = () => {
        drawer.classList.add("open");
        if (overlay) {
          overlay.classList.add("open");
          overlay.onclick = closeDrawer;
        }
      };
    }

    if (closeBtn) closeBtn.onclick = closeDrawer;

    if (clearBtn) {
      clearBtn.onclick = () => {
        this.resetAdvancedFilters();
        closeDrawer();
        setTimeout(() => this.render(container), 150);
      };
    }

    if (applyBtn) {
      applyBtn.onclick = () => {
        const catRadio = container.querySelector("input[name='cat_filter']:checked");
        if (catRadio) {
          this.activeCategory = catRadio.value;
          this.resetAdvancedFilters();
        }

        const sortSel = container.querySelector("#catalogSortSelectDrawer");
        if (sortSel) this.sortBy = sortSel.value;

        this.activeBrands.clear();
        container.querySelectorAll(".brand-filter-cb:checked").forEach(cb => {
          this.activeBrands.add(cb.value);
        });

        this.activeSubtypes.clear();
        container.querySelectorAll(".subtype-filter-cb:checked").forEach(cb => {
          this.activeSubtypes.add(cb.value);
        });

        const minVal = container.querySelector("#minPriceInput").value;
        const maxVal = container.querySelector("#maxPriceInput").value;
        this.minPrice = minVal ? parseFloat(minVal) : null;
        this.maxPrice = maxVal ? parseFloat(maxVal) : null;

        closeDrawer();
        setTimeout(() => this.render(container), 150);
      };
    }

    container.querySelectorAll(".color-swatch").forEach(swatch => {
      swatch.onclick = () => {
        const color = swatch.dataset.color;
        if (this.activeColors.has(color)) {
          this.activeColors.delete(color);
          swatch.classList.remove("selected");
        } else {
          this.activeColors.add(color);
          swatch.classList.add("selected");
        }
      };
    });
  }

  static renderSkeletons(count = 6) {
    return Array.from({ length: count }, () => `
      <div class="product-card-skeleton">
        <div class="skeleton skeleton-img"></div>
        <div class="skeleton-body">
          <div class="skeleton skeleton-line short"></div>
          <div class="skeleton skeleton-line title"></div>
          <div class="skeleton skeleton-line long"></div>
          <div class="skeleton skeleton-line price"></div>
        </div>
      </div>
    `).join("");
  }

  static renderProductCard(p, activeBike, wishlist) {
    const isWishlisted = wishlist ? wishlist.includes(p.id) : false;
    const utils = window.HRz.Utils;
    const escapeHTML = utils.escapeHTML;

    let displayImage = p.image;
    if (this.activeColors && this.activeColors.size > 0 && p.variants) {
      const matchingVar = p.variants.find(v => {
        const vCol = (v.color || "").toLowerCase();
        for (const ac of this.activeColors) {
          if (vCol.includes(ac.toLowerCase())) return true;
        }
        return false;
      });
      if (matchingVar && matchingVar.image) {
        displayImage = matchingVar.image;
      }
    }

    return `
      <div class="product-card reveal" data-id="${escapeHTML(p.id)}" style="cursor:pointer;">
        <div class="product-card-media">
          ${p.badge ? `<span class="product-badge">${escapeHTML(p.badge)}</span>` : ""}
          <button class="wishlist-toggle-btn ${isWishlisted ? "active" : ""}" data-id="${escapeHTML(p.id)}" aria-label="Toggle wishlist">
            ${isWishlisted ? "❤️" : "🤍"}
          </button>
          <img src="${escapeHTML(displayImage)}" alt="${escapeHTML(p.name)}" loading="lazy" onerror="this.src='images/helmet_product.webp'" />
        </div>
        <div class="product-card-content">
          <div class="card-category-strip">${escapeHTML(p.category)}</div>
          <h3 class="product-title">${escapeHTML(p.name)}</h3>
          <div class="price-action-row">
            <div class="price-lockup">
              <span class="current-price">${utils.formatCurrency(p.price)}</span>
              ${p.originalPrice ? `<span class="original-price">${utils.formatCurrency(p.originalPrice)}</span>` : ""}
            </div>
            <button class="accent-button add-to-cart-btn" data-id="${escapeHTML(p.id)}" ${!p.inStock ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
              ${p.inStock ? '+ Bag' : 'Out of Stock'}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  static bindCardEvents(container) {
    container.querySelectorAll(".product-card").forEach(card => {
      card.onclick = (e) => {
        if (e.target.closest(".wishlist-toggle-btn") || e.target.closest(".add-to-cart-btn")) {
          return;
        }
        const id = card.dataset.id;
        if (id) {
          let hash = `product?id=${encodeURIComponent(id)}`;
          if (window.HRz.Catalog.activeColors && window.HRz.Catalog.activeColors.size > 0) {
            const activeColor = Array.from(window.HRz.Catalog.activeColors)[0];
            hash += `&color=${encodeURIComponent(activeColor)}`;
          }
          window.location.hash = hash;
        }
      };
    });

    container.querySelectorAll(".wishlist-toggle-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        e.preventDefault();
        const id = btn.dataset.id;
        const isAdded = window.HRz.Storage.toggleWishlist(id);
        btn.classList.toggle("active", isAdded);
        btn.innerHTML = isAdded ? "❤️" : "🤍";
        window.HRz.Utils.showToast(isAdded ? "Added to Wishlist" : "Removed from Wishlist", "info");

        const countBadge = document.getElementById("wishlistCount");
        if (countBadge) countBadge.textContent = window.HRz.Storage.getWishlist().length;
      };
    });

    container.querySelectorAll(".add-to-cart-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        e.preventDefault();
        const id = btn.dataset.id;
        const prod = window.HRz.DB.getProductById(id);
        if (prod) {
          window.dispatchEvent(new CustomEvent("hrz:add-to-cart", { detail: { product: prod } }));
        }
      };
    });
  }
}

window.HRz.Catalog = CatalogView;
'''

with open("js/catalog.js", "w", encoding="utf-8") as f:
    f.write(catalog_js_code.strip() + "\n")

print("Successfully restored js/catalog.js to authentic UI design!")
