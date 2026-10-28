/* =============================================
   HRz PITSTOP – Product Catalog & Filtering Module
   Category & Dedicated Subcategory Sliders + Slide-out Drawer
   ============================================= */

window.HRz = window.HRz || {};

class CatalogView {
  static activeCategory = "All";
  static activeSubcategory = "All";
  static searchQuery = "";
  static sortBy = "featured";
  // Set by render() from smartSearch, before filtering/sorting (both strip
  // the flags from the returned array). The UI reads this to show the
  // "no exact fitment data for this bike" note — it is never a fitment claim.
  static searchFallback = false;
  static lastSearchQuery = "";
  static lastSearchNoExactFitment = false;
  static lastSearchIsBikeQuery = false;

  // Short display names -> canonical exact category names in products.json.
  // Task-specified aliases first; other keys are extra short forms that
  // resolve to the same real categories (no new categories invented).
  static CATEGORY_ALIASES = {
    "protection": "Bike Protection",
    "crash": "Bike Protection",
    "crash protection": "Bike Protection",
    "bike protection": "Bike Protection",
    "guards & mounts": "Bike Protection",
    "lights": "Lighting & Electrical",
    "light": "Lighting & Electrical",
    "lighting": "Lighting & Electrical",
    "lighting & electrical": "Lighting & Electrical",
    "luggage": "Luggage & Touring",
    "touring": "Luggage & Touring",
    "luggage & storage": "Luggage & Touring",
    "luggage & touring": "Luggage & Touring",
    "helmets": "Helmets & Accessories",
    "helmet": "Helmets & Accessories",
    "helmets & accessories": "Helmets & Accessories",
    "riding gears": "Riding Gears",
    "riding gear": "Riding Gears",
    "riding jackets & apparel": "Riding Gears",
    "gloves": "Riding Gears",
    "maintenance": "Cleaning & Care",
    "cleaning & care": "Cleaning & Care",
    "maintenance & cleaning": "Cleaning & Care"
  };

  static _realCategorySet() {
    const products = (window.HRz.DB && window.HRz.DB.products) || [];
    if (this._realCatCacheFor !== products || this._realCatCacheLen !== products.length) {
      const set = new Set();
      products.forEach(p => { if (p.category) set.add(String(p.category).toLowerCase()); });
      this._realCatCache = set;
      this._realCatCacheFor = products;
      this._realCatCacheLen = products.length;
    }
    return this._realCatCache || new Set();
  }

  // Resolve any category input to the canonical value used for filtering:
  // Alias map wins first to map historical or short routes (like "Lighting & Electrical" or "lights"),
  // then exact real category names, then normalisation.
  static resolveCategory(cat) {
    if (!cat || cat === "All") return "All";
    const trimmed = String(cat).trim();
    const alias = this.CATEGORY_ALIASES[trimmed.toLowerCase()];
    if (alias) return alias;
    const exact = [...this._realCategorySet()].find(c => c === trimmed.toLowerCase());
    if (exact) {
      const products = (window.HRz.DB && window.HRz.DB.products) || [];
      const hit = products.find(p => (p.category || "").toLowerCase() === exact);
      return hit ? hit.category : trimmed;
    }
    return this.normalizeCategory(trimmed);
  }

  // Department pill that owns a resolved category (for the active-pill
  // highlight). Exact categories with no pill (e.g. Covers) return
  // themselves, so no pill is wrongly highlighted.
  static departmentForCategory(cat) {
    if (!cat || cat === "All") return "All";
    const deptIds = this.DEPARTMENTS.map(d => d.id);
    if (deptIds.includes(cat)) return cat;
    for (const dept of this.DEPARTMENTS) {
      if (dept.id === "All") continue;
      if (this.isProductInDepartment({ category: cat }, dept.id)) return dept.id;
    }
    return cat;
  }

  // Single reusable sort entry point (home bestsellers reuse this).
  // Delegates to Utils.sortProducts; never mutates the input array.
  static sortProducts(products, sortBy) {
    if (window.HRz.Utils && window.HRz.Utils.sortProducts) {
      return window.HRz.Utils.sortProducts(products, sortBy);
    }
    const list = Array.isArray(products) ? [...products] : [];
    if (!sortBy || sortBy === "featured") {
      const isAcc = (p) => (window.HRz.Utils && window.HRz.Utils.isAccessoryProduct) ? (window.HRz.Utils.isAccessoryProduct(p) ? 1 : 0) : 0;
      const decorated = list.map((p, i) => ({ p, i, acc: isAcc(p) }));
      decorated.sort((a, b) => (a.acc - b.acc) || (a.i - b.i));
      return decorated.map(d => d.p);
    }
    const decorated = list.map((p, i) => ({ p, i }));
    decorated.sort((a, b) => {
      let cmp = 0;
      if (sortBy === "price-low") cmp = Number(a.p.price) - Number(b.p.price);
      else if (sortBy === "price-high") cmp = Number(b.p.price) - Number(a.p.price);
      else if (sortBy === "rating") cmp = (Number(b.p.rating) || 0) - (Number(a.p.rating) || 0);
      else if (sortBy === "name") cmp = String(a.p.name || "").localeCompare(String(b.p.name || ""));
      return cmp !== 0 ? cmp : a.i - b.i;
    });
    return decorated.map(d => d.p);
  }

  static validSort(sortBy) {
    if (window.HRz.Utils && window.HRz.Utils.isValidSort) return window.HRz.Utils.isValidSort(sortBy);
    return ["featured", "price-low", "price-high", "rating", "name"].includes(sortBy) ? sortBy : "featured";
  }

  // Department lookup used by the home filter buttons (previously
  // Catalog.getDepartment did not exist and home filters threw).
  static getDepartment(filter) {
    if (!filter || filter === "all") return { id: "All", name: "Shop All", matches: () => true };
    const resolved = this.resolveCategory(filter);
    return {
      id: resolved,
      name: resolved,
      matches: (p) => this.isProductInDepartment(p, resolved)
    };
  }

  static _readUrlParams() {
    try {
      const raw = (window.location.hash || "").replace(/^#/, "");
      const [, queryString] = raw.split("?");
      return new URLSearchParams(queryString || "");
    } catch (e) {
      return new URLSearchParams();
    }
  }

  // Persist the current sort in the URL (replaceState, no navigation) so
  // reload / back / shared links keep it. Featured is the default, so its
  // param is removed rather than stored.
  static syncSortToUrl() {
    try {
      const raw = (window.location.hash || "").replace(/^#/, "") || "catalog";
      const [base, queryString] = raw.split("?");
      const params = new URLSearchParams(queryString || "");
      if (this.sortBy && this.sortBy !== "featured") params.set("sort", this.sortBy);
      else params.delete("sort");
      const query = params.toString();
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, "", `#${base}${query ? "?" + query : ""}`);
      }
    } catch (e) { /* URL sync is best-effort; sort state itself is kept */ }
  }

  static _brandKey(brand) {
    if (window.HRz.Utils && window.HRz.Utils.normalizeBrandKey) return window.HRz.Utils.normalizeBrandKey(brand);
    return String(brand || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  }

  // Canonical real brand values whose normalised key matches `brand`
  // (e.g. "MotoTorque" -> ["Moto Torque"]). Empty when no real brand matches.
  static canonicalBrands(brand) {
    const products = (window.HRz.DB && window.HRz.DB.products) || [];
    const key = this._brandKey(brand);
    if (!key) return [];
    const seen = new Map();
    products.forEach(p => {
      if (p.brand && this._brandKey(p.brand) === key && !seen.has(p.brand)) seen.set(p.brand, p);
    });
    return [...seen.keys()];
  }

  static matchesBrand(product, brandSet) {
    if (!brandSet || brandSet.size === 0) return true;
    const productKey = this._brandKey(product.brand);
    for (const b of brandSet) {
      if (this._brandKey(b) === productKey) return true;
    }
    return false;
  }
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

  static DEPARTMENTS = [
    { id: "All", name: "Shop All", slug: "catalog" },
    { id: "Helmets & Accessories", name: "Helmets", slug: "helmets" },
    { id: "Riding Gears", name: "Riding Gear", slug: "riding-gears" },
    { id: "Bike Protection", name: "Bike Protection", slug: "protection" },
    { id: "Luggage & Touring", name: "Luggage & Touring", slug: "luggage" },
    { id: "Lighting & Electrical", name: "Lighting & Electrical", slug: "lights" },
    { id: "Handlebar & Accessories", name: "Handlebars", slug: "handlebars" },
    { id: "Performance Accessories", name: "Performance", slug: "performance" },
    { id: "Cleaning & Care", name: "Cleaning & Care", slug: "maintenance" }
  ];

  static normalizeCategory(cat) {
    if (!cat || cat === "All") return "All";
    const c = cat.toLowerCase().trim();
    if (c === "helmets" || c === "helmet" || c.includes("helmet")) return "Helmets & Accessories";
    if (c.includes("gear") || c.includes("jacket") || c.includes("apparel") || c.includes("riding") || c === "gloves") return "Riding Gears";
    if (c.includes("protect") || c.includes("crash") || c.includes("guard")) return "Bike Protection";
    if (c.includes("luggage") || c.includes("touring") || c.includes("storage")) return "Luggage & Touring";
    if (c.includes("light") || c.includes("electron") || c.includes("horn")) return "Lighting & Electrical";
    if (c.includes("handlebar") || c.includes("grip") || c.includes("mirror")) return "Handlebar & Accessories";
    if (c.includes("perform") || c.includes("exhaust")) return "Performance Accessories";
    if (c.includes("maint") || c.includes("oil") || c.includes("clean")) return "Cleaning & Care";
    return cat;
  }

  static isProductInDepartment(p, category) {
    const norm = this.normalizeCategory(category);
    if (norm === "All") return true;

    const pCat = (p.category || "").toLowerCase().trim();

    if (norm === "Helmets & Accessories") {
      return pCat === "helmets & accessories" || pCat.includes("helmet");
    }
    if (norm === "Riding Gears") {
      return ["riding gears", "riding gear", "riding jackets & apparel", "gloves", "riding pants", "boots & footwear", "protective gear"].includes(pCat) || pCat.includes("riding");
    }
    if (norm === "Bike Protection") {
      return pCat === "bike protection" || pCat === "crash protection" || pCat === "guards & mounts" || pCat.includes("protection");
    }
    if (norm === "Luggage & Touring") {
      return pCat === "luggage & touring" || pCat === "luggage & storage" || pCat.includes("luggage") || pCat.includes("touring");
    }
    if (norm === "Lighting & Electrical") {
      return pCat === "lighting & electrical" || pCat === "lighting" || pCat.includes("light") || pCat.includes("horn") || pCat === "electronics";
    }
    if (norm === "Handlebar & Accessories") {
      return pCat === "handlebar & accessories" || pCat.includes("handlebar") || pCat.includes("grip") || pCat.includes("mirror");
    }
    if (norm === "Performance Accessories") {
      return ["performance accessories", "performance parts", "exhaust system", "drive & transmission", "braking components", "suspension components", "engine components", "cables & controls", "body parts & panels", "tyres & wheels"].includes(pCat) || pCat.includes("performance");
    }
    if (norm === "Cleaning & Care") {
      return ["cleaning & care", "engine oils & lubricants", "maintenance & cleaning", "tools & workshop equipment"].includes(pCat) || pCat.includes("clean") || pCat.includes("oil");
    }
    return pCat === String(category).toLowerCase().trim() || pCat.includes(norm.toLowerCase());
  }

  static getProductSubcategory(p) {
    const sub = (p.subcategory || "").trim();
    if (sub) return sub;

    const pCat = (p.category || "").trim();
    if (["Gloves", "Riding Gloves"].includes(pCat)) return "Riding Gloves";
    if (["Riding Pants"].includes(pCat)) return "Riding Pants";
    if (["Boots & Footwear"].includes(pCat)) return "Boots & Footwear";
    if (["Engine Oils & Lubricants"].includes(pCat)) return "Engine Oils & Lubricants";
    if (pCat.toLowerCase().includes("exhaust")) return "Exhausts";
    if (pCat.toLowerCase().includes("brak")) return "Brakes";
    if (pCat.toLowerCase().includes("suspension")) return "Suspension";

    const name = (p.name || "").toLowerCase();
    if (name.includes("crash guard") || name.includes("engine guard")) return "Crash Guards";
    if (name.includes("bash plate") || name.includes("skid plate")) return "Bash Plates";
    if (name.includes("slider")) return "Frame Sliders";
    if (name.includes("radiator")) return "Radiator Guards";
    if (name.includes("headlight grill") || name.includes("headlight guard")) return "Headlight Grills";

    return pCat || "Other";
  }

  static matchesSubcategory(p, targetSubcategory) {
    if (!targetSubcategory || targetSubcategory === "All") return true;
    const target = targetSubcategory.toLowerCase().trim();
    const pSub = this.getProductSubcategory(p).toLowerCase().trim();
    if (pSub === target) return true;
    if ((p.subcategory || "").toLowerCase().trim() === target) return true;

    const pName = (p.name || "").toLowerCase();
    if (pName.includes(target)) return true;
    return false;
  }

  static render(container, options = {}) {
    const isNavigation = options.category !== undefined || options.subcategory !== undefined
      || options.search !== undefined || options.sort !== undefined || options.brand !== undefined;
    const urlParams = this._readUrlParams();

    if (options.category !== undefined) {
      const resolved = this.resolveCategory(options.category);
      if (this.activeCategory !== resolved) {
        this.activeCategory = resolved;
        this.resetAdvancedFilters();
      } else {
        this.activeCategory = resolved;
      }
    }
    if (options.subcategory !== undefined) {
      this.activeSubcategory = options.subcategory;
    } else if (options.category !== undefined && options.subcategory === undefined) {
      this.activeSubcategory = "All";
    }

    if (options.search !== undefined) {
      if (this.searchQuery !== options.search) {
        this.searchQuery = options.search;
        this.resetAdvancedFilters();
      }
    } else if (options.category !== undefined) {
      this.searchQuery = "";
    }

    // Sort: explicit option wins; on navigation, the URL param wins over
    // the previous in-memory value (reload / shared link / back); on an
    // internal re-render (options empty) the in-memory value is kept, so
    // drawer/ pill actions are not clobbered by a stale hash.
    if (options.sort !== undefined) {
      this.sortBy = this.validSort(options.sort);
    } else if (isNavigation && urlParams.has("sort")) {
      this.sortBy = this.validSort(urlParams.get("sort"));
    } else if (isNavigation) {
      this.sortBy = "featured";
    }

    // Brand: explicit option or ?brand= URL param, normalised so
    // "MotoTorque" matches "Moto Torque". Applied AFTER the category /
    // search resets above, so a brand link is not wiped by them. A
    // navigation with no brand param clears a previous brand filter.
    if (options.brand !== undefined) {
      this.activeBrands.clear();
      if (options.brand && options.brand !== "All") {
        const canonical = this.canonicalBrands(options.brand);
        (canonical.length ? canonical : [options.brand]).forEach(b => this.activeBrands.add(b));
      }
    } else if (isNavigation && urlParams.has("brand")) {
      this.activeBrands.clear();
      const rawBrand = urlParams.get("brand");
      if (rawBrand && rawBrand !== "All") {
        const canonical = this.canonicalBrands(rawBrand);
        (canonical.length ? canonical : [rawBrand]).forEach(b => this.activeBrands.add(b));
      }
    } else if (isNavigation) {
      this.activeBrands.clear();
    }

    const activeBike = window.HRz.Storage.getActiveBike();
    const wishlist = window.HRz.Storage.getWishlist();
    const escapeHTML = window.HRz.Utils.escapeHTML;

    let allBaseProducts = window.HRz.DB.products || [];
    let products = [...allBaseProducts];

    if (this.searchQuery) {
      const searchResult = window.HRz.Utils.smartSearch(this.searchQuery, products, null);
      // Capture the fallback flags BEFORE filtering/sorting, which return
      // plain arrays and strip them. UI reads Catalog.searchFallback /
      // Catalog.lastSearchNoExactFitment for the "no exact fitment data"
      // note (set for bike-model queries as well as for empty matches).
      this.searchFallback = !!(searchResult && (searchResult.isFallback || searchResult.searchFallback || searchResult.noFitmentData));
      this.lastSearchQuery = this.searchQuery;
      this.lastSearchNoExactFitment = this.searchFallback;
      this.lastSearchIsBikeQuery = !!(searchResult && searchResult.isBikeQuery);
      products = searchResult;
    } else {
      this.searchFallback = false;
      this.lastSearchQuery = "";
      this.lastSearchNoExactFitment = false;
      this.lastSearchIsBikeQuery = false;
    }

    // Filter by Active Category
    if (this.activeCategory && this.activeCategory !== "All") {
      products = products.filter(p => this.isProductInDepartment(p, this.activeCategory));
    }

    // Current department base products for subcategories. In search mode
    // (menu links like #catalog?search=CRASH GUARD carry no category), the
    // subcategory row must reflect ONLY the search results — not all 1,747
    // products — otherwise a menu click shows the full Shop All chrome.
    const currentDeptProducts = (this.activeCategory && this.activeCategory !== "All")
      ? allBaseProducts.filter(p => this.isProductInDepartment(p, this.activeCategory))
      : (this.searchQuery ? products : allBaseProducts);

    // Filter by Active Subcategory
    if (this.activeSubcategory && this.activeSubcategory !== "All") {
      products = products.filter(p => this.matchesSubcategory(p, this.activeSubcategory));
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

    // Drawer "Subcategory" list: the REAL subcategories of the current scope
    // (same source as the pill row), for every category — not name-keyword
    // guesses for 4 hardcoded categories. Shown only on dedicated pages
    // (category/search); Shop All already lists every subcategory as pills.
    const availableSubtypes = new Set();
    let subtypeLabel = "Subcategory";
    const activeCatLower = (this.activeCategory || "").toLowerCase();
    if (activeCatLower === "helmets") subtypeLabel = "Helmet Type";
    else if (activeCatLower.includes("luggage")) subtypeLabel = "Luggage Type";
    else if (activeCatLower.includes("protection")) subtypeLabel = "Protection Type";
    else if (activeCatLower.includes("gear") || activeCatLower.includes("riding")) subtypeLabel = "Apparel Type";
    const isDedicatedScope = (this.activeCategory && this.activeCategory !== "All") || !!this.searchQuery;
    if (isDedicatedScope) {
      currentDeptProducts.forEach(p => {
        const sub = this.getProductSubcategory(p);
        if (sub) availableSubtypes.add(sub);
      });
    }

    if (this.activeBrands.size > 0) {
      // Normalised brand match: "MotoTorque" matches "Moto Torque",
      // "STUDDS" matches "Studds", etc.
      products = products.filter(p => this.matchesBrand(p, this.activeBrands));
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
        for (const st of this.activeSubtypes) {
          if (this.matchesSubcategory(p, st)) return true;
        }
        return false;
      });
    }

    if (this.minPrice !== null) products = products.filter(p => p.price >= this.minPrice);
    if (this.maxPrice !== null) products = products.filter(p => p.price <= this.maxPrice);

    // Sort AFTER all filtering/search, on a copy (sortProducts never
    // mutates the master array). Supports featured/price-low/price-high/
    // rating/name via the single reusable comparator.
    products = this.sortProducts(products, this.sortBy);

    const activeCategoryNorm = this.activeCategory;
    const isSearchPage = !this.searchQuery ? false : (activeCategoryNorm === "All");
    const pageTitle = activeCategoryNorm !== "All" ? activeCategoryNorm.toUpperCase()
      : (isSearchPage ? `RESULTS FOR "${this.searchQuery.toUpperCase()}"` : "PRODUCT CATALOG");
    const eyebrowText = activeCategoryNorm !== "All" ? `Explore Premium ${activeCategoryNorm}`
      : (isSearchPage ? "Search Results" : "Guaranteed Motorcycle Parts");

    let activeFilterCount = this.activeBrands.size + this.activeColors.size + this.activeSubtypes.size + (this.minPrice ? 1 : 0) + (this.maxPrice ? 1 : 0);

    // Build Category Pills (Row 1)
    const categoryPillsHTML = this.DEPARTMENTS.map(dept => {
      const isActive = this.departmentForCategory(activeCategoryNorm) === dept.id;
      const count = dept.id === "All"
        ? allBaseProducts.length
        : allBaseProducts.filter(p => this.isProductInDepartment(p, dept.id)).length;
      return `
        <button class="nav-pill cat-pill ${isActive ? 'active' : ''}" data-cat-id="${escapeHTML(dept.id)}" data-slug="${escapeHTML(dept.slug)}">
          <span>${escapeHTML(dept.name)}</span>
          <span class="pill-count">${count}</span>
        </button>
      `;
    }).join("");

    // Build Subcategory Pills (Row 2) for the currently selected category
    const subcatCounts = {};
    currentDeptProducts.forEach(p => {
      const sub = this.getProductSubcategory(p);
      if (sub) {
        subcatCounts[sub] = (subcatCounts[sub] || 0) + 1;
      }
    });

    const isAllSubActive = !this.activeSubcategory || this.activeSubcategory === "All";
    const allSubLabel = activeCategoryNorm !== "All" ? `All ${activeCategoryNorm}`
      : (isSearchPage ? "All Results" : "Shop All");

    let subcategoryPillsHTML = `
      <button class="nav-pill subcat-pill ${isAllSubActive ? 'active' : ''}" data-subcat="All">
        <span>${escapeHTML(allSubLabel)}</span>
        <span class="pill-count">${currentDeptProducts.length}</span>
      </button>
    `;

    const sortedSubcats = Object.keys(subcatCounts).sort((a, b) => a.localeCompare(b));
    subcategoryPillsHTML += sortedSubcats.map(sub => {
      const isSubActive = !isAllSubActive && (this.activeSubcategory.toLowerCase() === sub.toLowerCase());
      return `
        <button class="nav-pill subcat-pill ${isSubActive ? 'active' : ''}" data-subcat="${escapeHTML(sub)}">
          <span>${escapeHTML(sub)}</span>
          <span class="pill-count">${subcatCounts[sub]}</span>
        </button>
      `;
    }).join("");

    container.innerHTML = `
      <div class="breadcrumb-trail">
        <a href="#home">Home</a> / ${activeCategoryNorm === "All"
          ? (isSearchPage
            ? `<a href="#catalog">Shop All</a> / <span class="current">Search: "${escapeHTML(this.searchQuery)}"</span>`
            : `<span class="current">Shop All</span>`)
          : `<a href="#catalog">Shop All</a> / <span class="current">${escapeHTML(activeCategoryNorm)}</span>`}
      </div>

      <div class="view-header">
        <div>
          <p class="eyebrow red">${escapeHTML(eyebrowText)}</p>
          <h2>${escapeHTML(pageTitle)}</h2>
        </div>
      </div>

      <div class="catalog-container inner-section" style="padding-top: 10px;">
        <!-- CATEGORY & DEDICATED SUBCATEGORY SLIDERS -->
        <div class="catalog-nav-bars">
          ${activeCategoryNorm === "All" && !isSearchPage ? `
          <!-- Row 1: Category Slider (Shop All only) -->
          <div class="scrollable-nav-wrapper category-nav-wrapper">
            <button class="scroll-arrow-btn prev" data-target="catTrack" aria-label="Scroll categories left">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
            </button>
            <div class="catalog-slider-track" id="catTrack">
              ${categoryPillsHTML}
            </div>
            <button class="scroll-arrow-btn next" data-target="catTrack" aria-label="Scroll categories right">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
          </div>
          ` : (isSearchPage ? `
          <!-- Search page bar: back to Shop All + result count (no global category row here) -->
          <div class="category-page-bar">
            <a href="#catalog" class="back-to-categories">← Shop All</a>
            <span class="category-page-count">${currentDeptProducts.length} results for "${escapeHTML(this.searchQuery)}"</span>
          </div>
          ` : `
          <!-- Category page bar: back to all categories + count (no global category row here) -->
          <div class="category-page-bar">
            <a href="#catalog" class="back-to-categories">← All Categories</a>
            <span class="category-page-count">${currentDeptProducts.length} products in ${escapeHTML(activeCategoryNorm)}</span>
          </div>
          `)}

          <!-- Row 2: Subcategory Slider (Dedicated to current category) -->
          <div class="scrollable-nav-wrapper subcategory-nav-wrapper">
            <button class="scroll-arrow-btn prev" data-target="subcatTrack" aria-label="Scroll subcategories left">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
            </button>
            <div class="catalog-slider-track" id="subcatTrack">
              ${subcategoryPillsHTML}
            </div>
            <button class="scroll-arrow-btn next" data-target="subcatTrack" aria-label="Scroll subcategories right">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
          </div>
        </div>

        <!-- Filter & Sort Bar (No duplicate count banner) -->
        <div class="view-header" style="padding: 0; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px;">
           <button class="open-filter-btn" id="openFilterDrawerBtn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
              Filter & Sort ${activeFilterCount > 0 ? `<span class="filter-count-badge">${activeFilterCount}</span>` : ''}
           </button>
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
            <h3>Filter ${activeCategoryNorm !== "All" ? activeCategoryNorm : "Products"}</h3>
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
                  <option value="name" ${this.sortBy === "name" ? "selected" : ""}>Name: A to Z</option>
                </select>
              </div>
            </div>

            ${activeCategoryNorm === "All" ? `
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

    this.bindSliderEvents(container);
    this.bindDrawerEvents(container);

    const resetBtnMain = container.querySelector("#resetCatalogFiltersBtnMain");
    if (resetBtnMain) {
      resetBtnMain.onclick = () => {
        this.resetAllFilters();
        this.render(container);
      };
    }

    const grid = container.querySelector("#catalogProductGrid");
    if (grid && products.length > 0) {
      setTimeout(() => {
        grid.innerHTML = products.map(p => this.renderProductCard(p, activeBike, wishlist)).join("");
        this.bindCardEvents(container);
      }, 120);
    }
  }

  static resetAdvancedFilters() {
    this.activeBrands.clear();
    this.activeColors.clear();
    this.activeSubtypes.clear();
    this.minPrice = null;
    this.maxPrice = null;
  }

  static resetAllFilters() {
    // Full reset: advanced filters PLUS category, subcategory, search and
    // sort, with catalog URL params stripped so a reload does not restore
    // the cleared filters. Used by both Reset buttons.
    this.resetAdvancedFilters();
    this.activeCategory = "All";
    this.activeSubcategory = "All";
    this.searchQuery = "";
    this.sortBy = "featured";
    try {
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, "", "#catalog");
      }
    } catch (e) { /* URL cleanup is best-effort; in-memory state is cleared */ }
  }

  static bindSliderEvents(container) {
    // Arrow buttons scrolling
    container.querySelectorAll(".scroll-arrow-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        const targetId = btn.dataset.target;
        const track = container.querySelector(`#${targetId}`);
        if (track) {
          const scrollAmt = btn.classList.contains("prev") ? -280 : 280;
          track.scrollBy({ left: scrollAmt, behavior: "smooth" });
        }
      };
    });

    // Drag-to-scroll support
    container.querySelectorAll(".catalog-slider-track").forEach(track => {
      let isDown = false;
      let startX, scrollLeft;
      track.addEventListener("mousedown", (e) => {
        isDown = true;
        startX = e.pageX - track.offsetLeft;
        scrollLeft = track.scrollLeft;
      });
      track.addEventListener("mouseleave", () => { isDown = false; });
      track.addEventListener("mouseup", () => { isDown = false; });
      track.addEventListener("mousemove", (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - track.offsetLeft;
        const walk = (x - startX) * 1.5;
        track.scrollLeft = scrollLeft - walk;
      });
    });

    // Category pills click — preserve the sort param in the URL so a
    // sort chosen in the drawer survives a category change (the router
    // passes sort through via Catalog.render's URL-param reading).
    container.querySelectorAll(".cat-pill").forEach(pill => {
      pill.onclick = (e) => {
        e.preventDefault();
        const catId = pill.dataset.catId;
        const slug = pill.dataset.slug;
        this.activeCategory = catId;
        this.activeSubcategory = "All";
        this.resetAdvancedFilters();

        const sortSuffix = (this.sortBy && this.sortBy !== "featured")
          ? `?sort=${encodeURIComponent(this.sortBy)}` : "";
        if (slug && slug !== "catalog") {
          window.location.hash = slug + sortSuffix;
        } else {
          window.location.hash = "catalog" + sortSuffix;
        }
      };
    });

    // Subcategory pills click
    container.querySelectorAll(".subcat-pill").forEach(pill => {
      pill.onclick = (e) => {
        e.preventDefault();
        const sub = pill.dataset.subcat;
        this.activeSubcategory = sub;

        const rawHash = window.location.hash.replace("#", "") || "catalog";
        const [baseRoute, queryString] = rawHash.split("?");
        const params = new URLSearchParams(queryString || "");

        if (sub === "All") {
          params.delete("subcategory");
        } else {
          params.set("subcategory", sub);
        }

        const query = params.toString();
        const newHash = query ? `${baseRoute}?${query}` : baseRoute;
        if (window.history && window.history.replaceState) {
          window.history.replaceState(null, "", `#${newHash}`);
        }

        this.render(container);
      };
    });

    // Center active pill in viewport
    setTimeout(() => {
      container.querySelectorAll(".catalog-slider-track").forEach(track => {
        const activePill = track.querySelector(".nav-pill.active");
        if (activePill) {
          activePill.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
        }
      });
    }, 60);
  }

  static bindDrawerEvents(container) {
    const drawer = container.querySelector("#catalogFilterDrawer");
    const openBtn = container.querySelector("#openFilterDrawerBtn");
    const closeBtn = container.querySelector("#closeFilterDrawerBtn");
    const clearBtn = container.querySelector("#clearFiltersBtn");
    const applyBtn = container.querySelector("#applyFiltersBtn");
    const overlay = document.getElementById("overlay");

    const closeDrawer = () => {
      drawer?.classList.remove("open");
      overlay?.classList.remove("open");
    };

    if (openBtn) {
      openBtn.onclick = () => {
        drawer?.classList.add("open");
        overlay?.classList.add("open");
      };
    }

    if (closeBtn) closeBtn.onclick = closeDrawer;

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

    if (clearBtn) {
      clearBtn.onclick = () => {
        this.resetAllFilters();
        closeDrawer();
        setTimeout(() => this.render(container), 150);
      };
    }

    if (applyBtn) {
      applyBtn.onclick = () => {
        const catRadio = container.querySelector("input[name='cat_filter']:checked");
        if (catRadio) {
          this.activeCategory = catRadio.value;
          this.activeSubcategory = "All";
          this.resetAdvancedFilters();
        }

        const sortSel = container.querySelector("#catalogSortSelectDrawer");
        if (sortSel) this.sortBy = this.validSort(sortSel.value);
        // Persist sort in the URL so reload / back / shared links keep it.
        this.syncSortToUrl();

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

    // Cart quantity for this product (0 when not in the bag). The card
    // action then renders as a - qty + stepper instead of a static + Bag.
    // Family total: the base id is the default variant, suffixed ids are
    // other variants — so the card never disagrees with the product page
    // about how many of this product are in the bag.
    const cartQty = this.getFamilyQty(p.id);

    // Discount badge: only when a genuine strikethrough price exists.
    const discountPct = (p.originalPrice && Number(p.originalPrice) > Number(p.price))
      ? Math.round((1 - Number(p.price) / Number(p.originalPrice)) * 100) : 0;

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
          ${(p.availableSizes && p.availableSizes.length > 0) ? `
            <div class="card-size-preview">
              ${p.availableSizes.slice(0, 4).map(s => `<span class="card-size-chip">${escapeHTML(s)}</span>`).join("")}
              ${p.availableSizes.length > 4 ? `<span class="card-size-chip more">+${p.availableSizes.length - 4}</span>` : ""}
            </div>
          ` : ""}
          <div class="price-action-row">
            <div class="price-lockup">
              <span class="current-price">${utils.formatCurrency(p.price)}</span>
              ${(p.originalPrice && Number(p.originalPrice) > Number(p.price)) ? `<span class="original-price">${utils.formatCurrency(p.originalPrice)}</span>` : ""}
              ${discountPct > 0 ? `<span class="discount-badge">${discountPct}% OFF</span>` : ""}
            </div>
            ${!p.inStock ? `
            <button class="accent-button add-to-cart-btn" data-id="${escapeHTML(p.id)}" disabled style="opacity: 0.5; cursor: not-allowed;">
              Out of Stock
            </button>
            ` : (cartQty > 0 ? `
            <div class="card-qty-stepper" data-id="${escapeHTML(p.id)}">
              <button class="qty-btn card-qty-minus" data-id="${escapeHTML(p.id)}" aria-label="Decrease quantity">−</button>
              <span class="qty-num">${cartQty}</span>
              <button class="qty-btn card-qty-plus" data-id="${escapeHTML(p.id)}" aria-label="Increase quantity">+</button>
            </div>
            ` : `
            <button class="accent-button add-to-cart-btn" data-id="${escapeHTML(p.id)}">
              + Bag
            </button>
            `)}
          </div>
        </div>
      </div>
    `;
  }

  static bindCardEvents(container) {
    container.querySelectorAll(".product-card").forEach(card => {
      card.onclick = (e) => {
        if (e.target.closest(".wishlist-toggle-btn") || e.target.closest(".add-to-cart-btn") || e.target.closest(".card-qty-stepper")) {
          return;
        }
        const id = card.dataset.id;
        if (id) {
          const prodObj = window.HRz.DB ? window.HRz.DB.getProductById(id) : null;
          let hash = `product?id=${encodeURIComponent(id)}`;
          if (window.HRz.Catalog.activeColors && window.HRz.Catalog.activeColors.size > 0) {
            const activeColor = Array.from(window.HRz.Catalog.activeColors)[0];
            hash += `&color=${encodeURIComponent(activeColor)}`;
          } else if (prodObj && prodObj.variants && prodObj.variants.length) {
            const matchedVar = prodObj.variants.find(v => v.id === id);
            if (matchedVar && matchedVar.color) {
              hash += `&color=${encodeURIComponent(matchedVar.color)}`;
            }
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
          const toAdd = { ...prod };
          if (Array.isArray(toAdd.availableSizes) && toAdd.availableSizes.length > 0) {
            toAdd.selectedSize = toAdd.availableSizes[0];
          }
          window.dispatchEvent(new CustomEvent("hrz:add-to-cart", { detail: { product: toAdd } }));
          this.syncCardCartButton(btn);
        }
      };
    });

    // Card quantity stepper (- qty +): plus/minus update the bag, and the
    // button swaps back to + Bag when the quantity reaches zero. Steps
    // resolve to the real bag entry (base first, else a variant entry),
    // since the card shows the family total, not one entry.
    container.querySelectorAll(".card-qty-minus, .card-qty-plus").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        e.preventDefault();
        const id = btn.dataset.id;
        const delta = btn.classList.contains("card-qty-plus") ? 1 : -1;
        const entryId = this.resolveFamilyEntryId(id) || id;
        if (window.HRz.Cart && typeof window.HRz.Cart.updateQuantity === "function") {
          window.HRz.Cart.updateQuantity(entryId, delta);
        }
        this.syncCardCartButton(btn);
      };
    });
  }

  // Bag identity shared by cards and the product page: the base id is the
  // default variant, suffixed ids (base + "-" + slug) are other variants.
  static getFamilyQty(productId) {
    try {
      const cart = (window.HRz.Storage && typeof window.HRz.Storage.getCart === "function") ? window.HRz.Storage.getCart() : [];
      return cart.reduce((sum, i) => {
        if (i.id === productId || (typeof i.id === "string" && i.id.startsWith(productId + "-"))) return sum + (Number(i.quantity) || 0);
        return sum;
      }, 0);
    } catch (e) { return 0; }
  }

  static resolveFamilyEntryId(productId) {
    try {
      const cart = (window.HRz.Storage && typeof window.HRz.Storage.getCart === "function") ? window.HRz.Storage.getCart() : [];
      const base = cart.find(i => i.id === productId);
      if (base) return base.id;
      const variant = cart.find(i => typeof i.id === "string" && i.id.startsWith(productId + "-"));
      return variant ? variant.id : null;
    } catch (e) { return null; }
  }

  // Re-render one card's action area from the live bag state: + Bag becomes
  // a stepper on first add, the stepper number follows quantity changes,
  // and it reverts to + Bag when the last unit is removed.
  static syncCardCartButton(anchorEl) {
    try {
      const card = anchorEl.closest ? anchorEl.closest(".product-card") : null;
      if (!card) return;
      const id = (anchorEl.dataset && anchorEl.dataset.id) || (card.dataset && card.dataset.id);
      if (!id) return;
      const qty = this.getFamilyQty(id);
      const row = card.querySelector(".price-action-row");
      if (!row) return;
      const oldBtn = row.querySelector(".add-to-cart-btn");
      const oldStepper = row.querySelector(".card-qty-stepper");
      if (qty > 0) {
        if (oldStepper) {
          const num = oldStepper.querySelector(".qty-num");
          if (num) num.textContent = String(qty);
        } else if (oldBtn) {
          oldBtn.outerHTML = `<div class="card-qty-stepper" data-id="${id}">
            <button class="qty-btn card-qty-minus" data-id="${id}" aria-label="Decrease quantity">−</button>
            <span class="qty-num">${qty}</span>
            <button class="qty-btn card-qty-plus" data-id="${id}" aria-label="Increase quantity">+</button>
          </div>`;
          this.bindCardEvents(card);
        }
      } else if (oldStepper) {
        oldStepper.outerHTML = `<button class="accent-button add-to-cart-btn" data-id="${id}">+ Bag</button>`;
        this.bindCardEvents(card);
      }
    } catch (e) { /* a stale card button must never break the page */ }
  }
}

window.HRz.Catalog = CatalogView;
