/* =============================================
   HRz PITSTOP – Main Application Entry & Router Module
   Adapted for editorial "Rogue Ride" design
   ============================================= */

window.HRz = window.HRz || {};

class App {
  static async init() {
    console.log("Initializing HRz Pitstop application...");

    await window.HRz.DB.init();
    this.syncDataLoadBanner();

    window.HRz.Garage.init((activeBike) => this.onBikeChanged(activeBike));
    window.HRz.Cart.init();
    window.HRz.Search.init();
    if (window.HRz.Auth) window.HRz.Auth.init();
    if (window.HRz.Menu) window.HRz.Menu.init();

    window.addEventListener("hashchange", () => this.handleRoute());
    this.bindNavigation();
    this.bindGlobalUI();

    this.handleRoute();
  }

  static onBikeChanged(activeBike) {
    const currentHash = window.location.hash.replace("#", "").split("?")[0];
    if (currentHash === "catalog" || currentHash === "" || currentHash === "home") {
      this.handleRoute();
    }
  }

  static bindNavigation() {
    // Main nav links
    document.querySelectorAll(".main-nav .nav-link").forEach(link => {
      link.onclick = (e) => {
        e.preventDefault();
        const view = link.dataset.view;
        if (view) window.location.hash = view;
      };
    });

    // Footer links and other data-view-target links
    document.querySelectorAll("[data-view-target]").forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        const target = btn.dataset.viewTarget;
        const filter = btn.dataset.filter;
        if (filter) {
          window.location.hash = `catalog?category=${encodeURIComponent(filter)}`;
        } else if (target) {
          window.location.hash = target;
        }
      };
    });

    // Wishlist nav button
    const wishlistBtn = document.getElementById("wishlistNavBtn");
    if (wishlistBtn) {
      wishlistBtn.onclick = () => { window.location.hash = "wishlist"; };
    }
  }

  static bindGlobalUI() {
    const overlay = document.getElementById("overlay");
    const searchBtn = document.getElementById("searchBtn");
    const closeSearchBtn = document.getElementById("closeSearchBtn");
    const searchPanel = document.getElementById("searchPanel");
    const mobileSearch = document.getElementById("mobileSearch");
    const mobileCart = document.getElementById("mobileCart");

    // Search panel
    if (searchBtn) searchBtn.onclick = () => this.openPanel(searchPanel);
    if (closeSearchBtn) closeSearchBtn.onclick = () => this.closeAllPanels();
    if (mobileSearch) mobileSearch.onclick = () => this.openPanel(searchPanel);
    if (mobileCart) mobileCart.onclick = () => document.getElementById("openCartBtn")?.click();

    // Overlay closes everything
    if (overlay) overlay.onclick = () => this.closeAllPanels();

    // Sync mobile cart count
    this.syncMobileCartCount();

    // Sync wishlist dock badge, live. Wrap Storage.toggleWishlist once so
    // every toggle (cards, product page) refreshes the dock badge.
    this.syncWishlistBadge();
    if (window.HRz.Storage && typeof window.HRz.Storage.toggleWishlist === "function" && !window.HRz.Storage.__hrzWishlistSyncWrapped) {
      const origToggle = window.HRz.Storage.toggleWishlist;
      window.HRz.Storage.toggleWishlist = function (...args) {
        const result = origToggle.apply(this, args);
        App.syncWishlistBadge();
        return result;
      };
      window.HRz.Storage.__hrzWishlistSyncWrapped = true;
    }
    window.addEventListener("storage", () => this.syncWishlistBadge());

    // Scroll action for mobile dock
    let lastScrollY = window.scrollY;
    const dock = document.querySelector(".mobile-dock");
    window.addEventListener("scroll", () => {
      if (!dock) return;
      const currentScrollY = window.scrollY;
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        dock.classList.add("hidden");
      } else {
        dock.classList.remove("hidden");
      }
      lastScrollY = currentScrollY;
    }, { passive: true });

    // Handle mobile back button for panels
    window.addEventListener("popstate", (e) => {
      const overlay = document.getElementById("overlay");
      if (overlay && overlay.classList.contains("open")) {
        this.closeAllPanels(true); // true = called from popstate, don't trigger back() again
      }
      const viewer = document.getElementById("productGalleryViewer");
      if (viewer && viewer.classList.contains("open")) {
        if (window.HRz.Product && window.HRz.Product.closeViewer) {
          window.HRz.Product.closeViewer(true);
        } else {
          viewer.classList.remove("open");
          document.body.classList.remove("gallery-viewer-open");
        }
      }
      const fitmentModal = document.getElementById("fitmentReportModal");
      if (fitmentModal && fitmentModal.classList.contains("show")) {
        fitmentModal.classList.remove("show");
      }
      const orderModal = document.getElementById("orderDetailsModal");
      if (orderModal && orderModal.classList.contains("open")) {
        this.closeOrderDetailsModal(true);
      }
    });
  }

  static openPanel(panel) {
    if (!panel) return;
    panel.classList.add("open");
    document.getElementById("overlay")?.classList.add("open");
    
    // Push state so Android back button works
    if (!window.history.state || !window.history.state.panelOpen) {
      window.history.pushState({ panelOpen: true }, "");
    }
    
    const input = panel.querySelector("input");
    if (input) setTimeout(() => input.focus(), 100);
  }

  static closeAllPanels(isPopState = false, skipHistory = false) {
    const overlay = document.getElementById("overlay");
    const wasOpen = overlay && overlay.classList.contains("open");

    document.getElementById("overlay")?.classList.remove("open");
    document.getElementById("searchPanel")?.classList.remove("open");
    const searchInput = document.getElementById("globalSearch");
    if (searchInput) searchInput.value = "";
    const searchResults = document.getElementById("searchAutocomplete");
    if (searchResults) searchResults.innerHTML = "";
    document.getElementById("quickView")?.classList.remove("open");
    document.getElementById("cartDrawer")?.classList.remove("open");
    document.getElementById("catalogFilterDrawer")?.classList.remove("open");
    if (window.HRz.Menu) window.HRz.Menu.closeAll(true);
    
    // If it was closed manually (not via back button), remove the history state
    if (wasOpen && !isPopState && window.history.state && window.history.state.panelOpen) {
      if (!skipHistory) {
        window.history.back();
      } else {
        window.history.replaceState({}, "");
      }
    }
  }

  static syncMobileCartCount() {
    const mainBadge = document.getElementById("cartCountBadge");
    const mobileBadge = document.getElementById("mobileCartCount");
    if (mainBadge && mobileBadge) {
      new MutationObserver(() => {
        mobileBadge.textContent = mainBadge.textContent;
      }).observe(mainBadge, { childList: true, characterData: true, subtree: true });
    }
  }

  // Shared home sorter (UI worker). Prefer the logic worker's shared
  // sorter window.HRz.Catalog.sortProducts(products, sortBy) when present;
  // otherwise use this local copy of the same comparators. FLAG FOR MERGE:
  // coordinator must verify window.HRz.Catalog.sortProducts exists at merge
  // time and that the home sort then routes through it, not this fallback.
  static homeSortProducts(products, sortBy) {
    const list = [...(products || [])];
    const shared = window.HRz && window.HRz.Catalog &&
      typeof window.HRz.Catalog.sortProducts === "function"
      ? window.HRz.Catalog.sortProducts : null;
    if (shared) {
      try {
        const out = shared([...list], sortBy);
        if (Array.isArray(out)) return out;
      } catch (e) { /* fall through to local comparators */ }
    }
    const price = (p) => { const n = Number(p && p.price); return Number.isFinite(n) ? n : 0; };
    const rating = (p) => { const n = Number(p && p.rating); return Number.isFinite(n) ? n : 0; };
    const name = (p) => String((p && p.name) || "");
    if (sortBy === "price-low") return list.sort((a, b) => price(a) - price(b) || name(a).localeCompare(name(b)));
    if (sortBy === "price-high") return list.sort((a, b) => price(b) - price(a) || name(a).localeCompare(name(b)));
    if (sortBy === "rating") return list.sort((a, b) => rating(b) - rating(a) || ((b.reviewCount || 0) - (a.reviewCount || 0)) || name(a).localeCompare(name(b)));
    if (sortBy === "name") return list.sort((a, b) => name(a).localeCompare(name(b)));
    const isAcc = (p) => (window.HRz && window.HRz.Utils && window.HRz.Utils.isAccessoryProduct) ? (window.HRz.Utils.isAccessoryProduct(p) ? 1 : 0) : 0;
    return list.map((p, i) => ({ p, i, acc: isAcc(p) })).sort((a, b) => (a.acc - b.acc) || (a.i - b.i)).map(d => d.p);
  }

  // Home filter without the app.js:588 crash. If Catalog.getDepartment()
  // exists (logic worker), use it; otherwise fall back to the existing
  // Catalog.isProductInDepartment(), and finally to a plain category match.
  // Prioritises primary core products first before slicing to top 8.
  static getHomeFilteredProducts(filter, activeBike, db) {
    if (!filter || filter === "all") {
      return db.getRecommendedProducts(activeBike, null, 8);
    }
    const base = (db.getProductsForBike ? db.getProductsForBike(activeBike) : []) || [];
    const C = window.HRz.Catalog;
    // "Fog Lights" is a subcategory, not a department: match Fog & Aux Lights
    // only. The old path resolved "Lights" to the whole Lighting department,
    // which also swallowed the Electronics category (intercoms, GPS mounts).
    let matched = [];
    if (filter === "Lights") {
      matched = base.filter(p => {
        try {
          const sub = (C && typeof C.getProductSubcategory === "function") ? C.getProductSubcategory(p) : (p.subcategory || "");
          return sub === "Fog & Aux Lights";
        } catch (e) { return false; }
      });
    } else {
      let dept = null;
      try { dept = (C && typeof C.getDepartment === "function") ? C.getDepartment(filter) : null; } catch (e) { dept = null; }
      if (dept && typeof dept.matches === "function") {
        matched = base.filter(p => { try { return dept.matches(p); } catch (e) { return false; } });
      } else if (typeof dept === "string" && C && typeof C.isProductInDepartment === "function") {
        matched = base.filter(p => C.isProductInDepartment(p, dept));
      } else if (C && typeof C.isProductInDepartment === "function") {
        matched = base.filter(p => C.isProductInDepartment(p, filter));
      } else {
        matched = base.filter(p => (p.category || "") === filter);
      }
    }
    const sorted = App.homeSortProducts(matched, "featured");
    return sorted.slice(0, 8);
  }

  // Live wishlist count for the dock badge. Called on route changes and
  // whenever the wishlist changes (wrapped toggle + storage events).
  static syncWishlistBadge() {
    try {
      const list = window.HRz.Storage ? window.HRz.Storage.getWishlist() : [];
      const count = Array.isArray(list) ? list.length : 0;
      document.querySelectorAll("#mobileWishlistCount, #wishlistCount").forEach(el => {
        el.textContent = String(count);
      });
    } catch (e) { /* badge is cosmetic; never break routing */ }
  }

  static syncDataLoadBanner() {
    const loadError = window.HRz.DB.loadError;
    const existing = document.getElementById("dataLoadErrorBanner");

    if (!loadError) {
      if (existing) existing.remove();
      return;
    }

    if (!existing) {
      const banner = document.createElement("div");
      banner.id = "dataLoadErrorBanner";
      banner.style.cssText = [
        "background:#8d1f18",
        "color:#fff",
        "padding:12px 16px",
        "font-size:14px",
        "line-height:1.4",
        "position:relative",
        "z-index:30"
      ].join(";");
      banner.innerHTML = `
        <strong>Data load failed:</strong>
        <span>${window.HRz.Utils.escapeHTML(loadError.message)}</span>
      `;
      const appRoot = document.getElementById("app");
      if (appRoot && appRoot.parentElement) {
        appRoot.parentElement.insertBefore(banner, appRoot);
      }
    } else {
      existing.innerHTML = `
        <strong>Data load failed:</strong>
        <span>${window.HRz.Utils.escapeHTML(loadError.message)}</span>
      `;
    }
  }

  static handleRoute() {
    this.syncDataLoadBanner();
    const rawHash = window.location.hash.replace("#", "") || "home";
    const [route, queryString] = rawHash.split("?");
    const params = new URLSearchParams(queryString || "");

    // Update nav active state
    document.querySelectorAll(".main-nav .nav-link").forEach(link => {
      link.classList.toggle("active", link.dataset.view === route);
    });
    // Dock mapping: product/checkout/tracking have no own dock item, so they
    // highlight the nearest one (Shop for product, Bag for checkout/tracking).
    // Garage has no dock item (it lives in the header/menu), so no dock
    // item is highlighted on the garage view.
    const dockMap = {
      home: "home", catalog: "catalog", models: "catalog", product: "catalog",
      helmets: "catalog", "riding-gears": "catalog", "riding-gear": "catalog",
      jackets: "catalog", protection: "catalog", "crash-guards": "catalog",
      luggage: "catalog", lights: "catalog", lighting: "catalog",
      performance: "catalog", maintenance: "catalog",
      wishlist: "wishlist", checkout: "bag", tracking: "bag"
    };
    const dockKey = dockMap[route] || null;
    document.querySelectorAll(".mobile-dock .dock-item").forEach(item => {
      item.classList.toggle("active", !!dockKey && item.dataset.dock === dockKey);
    });
    // Product pages own the bottom of the screen: the buy capsule sits
    // where the dock sits, so the dock itself is hidden there.
    document.body.classList.toggle("is-product-page", route === "product");
    this.syncWishlistBadge();

    const deptRoutes = ["helmets", "riding-gears", "riding-gear", "jackets", "protection", "crash-guards", "luggage", "lights", "lighting", "electronics", "performance", "maintenance"];
    const isDeptRoute = deptRoutes.includes(route);
    const viewId = isDeptRoute ? "catalog" : route;

    // Switch views
    document.querySelectorAll("#app .view").forEach(v => v.classList.remove("active"));
    const activeViewEl = document.getElementById(viewId) || document.getElementById("home");
    if (activeViewEl) {
      activeViewEl.classList.add("active");
      window.scrollTo(0, 0);
    }

    // Ensure footer is visible across all views
    const footer = document.getElementById("siteFooter");
    if (footer) footer.style.display = "flex";

    if (window.HRz.SEO) {
      window.HRz.SEO.updateSEOForView(route, {
        product: route === "product" ? window.HRz.DB.getProductById(params.get("id")) : null
      });
    }

    switch (route) {
      case "home":
        this.renderHomeView(activeViewEl);
        break;
      case "models":
        this.renderModelsView(activeViewEl, params.get("brand"));
        break;
      case "helmets":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Helmets",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "riding-gears":
      case "riding-gear":
      case "jackets":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Riding Gears",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "protection":
      case "crash-guards":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Protection",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "luggage":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Luggage",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "lights":
      case "lighting":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Lights",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "electronics":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Electronics",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "performance":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Performance",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "maintenance":
        window.HRz.Catalog.render(activeViewEl, {
          category: "Maintenance",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "catalog":
        window.HRz.Catalog.render(activeViewEl, {
          category: params.get("category") || "All",
          subcategory: params.get("subcategory") || "All",
          search: params.get("search") || ""
        });
        break;
      case "product":
        window.HRz.Product.render(activeViewEl, params.get("id"), params.get("color"));
        break;
      case "garage":
        window.HRz.Garage.renderGarageView(activeViewEl);
        break;
      case "checkout":
        window.HRz.Checkout.render(activeViewEl);
        break;
      case "admin":
        window.HRz.Admin.render(activeViewEl);
        break;
      case "wishlist":
        this.renderWishlistView(activeViewEl);
        break;
      case "tracking":
        this.renderTrackingView(activeViewEl);
        break;
      case "reviews":
        this.renderReviewsView(activeViewEl);
        break;
      case "help":
        this.renderHelpView(activeViewEl);
        break;
      case "about":
        if (window.HRz.Menu) window.HRz.Menu.renderAbout(activeViewEl);
        break;
      case "events":
        if (window.HRz.Menu) window.HRz.Menu.renderEvents(activeViewEl, params.get("tab") || "upcoming");
        break;
      default:
        this.renderHomeView(activeViewEl);
        break;
    }
  }

  static getWikiImage(query, imgEl, fallback) {
    const url = `https://en.wikipedia.org/w/api.php?origin=*&action=query&format=json&prop=pageimages&generator=search&gsrsearch=${encodeURIComponent(query)}&gsrlimit=1&pithumbsize=500`;
    fetch(url)
      .then(res => res.json())
      .then(data => {
        const pages = data.query && data.query.pages;
        if (pages) {
          const pageId = Object.keys(pages)[0];
          if (pages[pageId] && pages[pageId].thumbnail) {
            imgEl.src = pages[pageId].thumbnail.source;
            return;
          }
        }
      })
      .catch(() => {});
  }

  static renderHomeView(container) {
    const activeBike = window.HRz.Storage.getActiveBike();
    const heroBanner = window.HRz.Storage.getHeroBanner();
    const db = window.HRz.DB;
    const featuredProducts = db.getRecommendedProducts(null, null, 8);
    const utils = window.HRz.Utils;
    const catalog = window.HRz.Catalog;
    const wishlist = window.HRz.Storage.getWishlist();
    const categories = db.getProducts();
    const escapeHTML = utils.escapeHTML;
    const catImages = {
      Protection: "images/category_protection.webp",
      Helmets: "images/category_helmets.webp",
      Lights: "images/category_lights.webp",
      Luggage: "images/category_luggage.webp"
    };

    // Recently Viewed: only genuine history. Previously the section fell
    // back to bestsellers when empty, which mislabels them as viewed.
    const recentIds = window.HRz.Storage.getRecentlyViewed();
    const recentProducts = recentIds.map(id => window.HRz.DB.getProductById(id)).filter(p => p).slice(0, 4);

    container.innerHTML = `
      <!-- Hero -->
      <section class="hero">
        <img src="images/hero-rider.webp" alt="Motorcyclist and sport motorcycle in a dark garage" />
        <div class="hero-shade"></div>
        <div class="hero-copy">
          <p class="eyebrow">Built for every mile</p>
          <h1>GEAR UP.<br /><em>GO FAR.</em></h1>
          <p class="hero-text">Purpose-built protection and performance for riders who never take the easy road.</p>
          <a class="button button-red" href="#catalog">Browse collection <span>→</span></a>
        </div>
      </section>

      <!-- 3D Bike Selector -->
      <section class="bike-selector-3d section" id="bikeSelector3D">
        <div class="section-head">
          <div><p class="eyebrow red">Select your machine</p><h2>CHOOSE YOUR <em>BRAND</em></h2></div>
        </div>
        <div class="bike-slider-wrapper">
          <button class="bike-slider-nav prev" id="bikeSliderPrev" aria-label="Previous Brand">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
          </button>
          <div class="bike-slider-container">
            <div class="bike-slider">
              ${(() => {
                const brands = Object.keys(window.HRz.Menu.menuData.shopByBike);
                return [1, 2, 3].map(set => brands.map((brand, idx) => {
                  const brandModels = window.HRz.Menu.menuData.shopByBike[brand];
                  const firstModel = brandModels && brandModels.length > 0 ? brandModels[0] : null;
                  const imgUrl = (window.HRzImageMap && (window.HRzImageMap[brand] || (firstModel && window.HRzImageMap[firstModel]))) 
                    || `images/verified bikes/bike_images/${brand}.png`;
                  const uid = `brand-img-${set}-${idx}`;
                  return `
                  <div class="bike-item" data-brand="${escapeHTML(brand)}" data-set="${set}" data-index="${idx}" role="button" tabindex="0" aria-label="${escapeHTML(brand)}">
                    <div class="bike-img-wrap"><img id="${uid}" src="${imgUrl}" alt="${escapeHTML(brand)}" style="object-fit: contain; padding: 10px;" onerror="this.onerror=null; this.src=window.HRzPlaceholderImage;" loading="lazy" /></div>
                    <div class="bike-info"><h3>${escapeHTML(brand)}</h3></div>
                  </div>
                `;}).join('')).join('');
              })()}
            </div>
          </div>
          <button class="bike-slider-nav next" id="bikeSliderNext" aria-label="Next Brand">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>
        </div>
      </section>

      <!-- Categories -->
      <section class="categories section" id="categories">
        <div class="section-head">
          <div><p class="eyebrow red">Find your essential</p><h2>SHOP BY <em>CATEGORY</em></h2></div>
          <a href="#catalog" class="text-link">View all gear <span>→</span></a>
        </div>
        <div class="category-grid">
          <div class="category large" onclick="window.location.hash='#protection'">
            <video src="images/cat_vid_crash.mp4" autoplay loop muted playsinline class="category-vid"></video>
            
            <span><small>01</small> Crash Guards <b>→</b></span>
          </div>
          <div class="category" onclick="window.location.hash='#helmets'">
            <video src="images/cat_vid_helmet.mp4" autoplay loop muted playsinline class="category-vid"></video>
            
            <span><small>02</small> Helmets <b>→</b></span>
          </div>
          <div class="category" onclick="window.location.hash='#lights'">
            <video src="images/cat_vid_fog.mp4" autoplay loop muted playsinline class="category-vid"></video>
            
            <span><small>03</small> Fog Lights <b>→</b></span>
          </div>
          <div class="category" onclick="window.location.hash='#luggage'">
            <video src="images/cat_vid_luggage.mp4" autoplay loop muted playsinline class="category-vid"></video>
            
            <span><small>04</small> Luggage <b>→</b></span>
          </div>
        </div>
      </section>

      <!-- Bestsellers / Products -->
      <section class="products-section section" id="shop">
        <div class="section-head">
          <div><p class="eyebrow red">Rider approved</p><h2>THE <em>BESTSELLERS</em></h2></div>
          <div class="filters">
            <button class="active" data-filter="all">All Gear</button>
            <button data-filter="Helmets">Helmets</button>
            <button data-filter="Protection">Crash Guards</button>
            <button data-filter="Riding Gears">Riding Gear</button>
            <button data-filter="Lights">Fog Lights</button>
            <button data-filter="Luggage">Luggage</button>
          </div>
        </div>
        <div class="shop-toolbar">
          <span id="product-count">${featuredProducts.length} products</span>
          <div>
            <label>Sort <select id="home-sort-select">
              <option value="featured">Featured</option>
              <option value="price-low">Price: low to high</option>
              <option value="price-high">Price: high to low</option>
              <option value="rating">Customer rating</option>
              <option value="name">Name A to Z</option>
            </select></label>
          </div>
        </div>
        <div class="product-grid" id="home-product-grid">
          ${featuredProducts.map(p => catalog.renderProductCard(p, activeBike, wishlist)).join("")}
        </div>
      </section>

      <!-- Reviews -->
      <section class="reviews-section section">
        <div class="section-head">
          <div><p class="eyebrow red">The word on the street</p><h2>RIDER <em>REVIEWS</em></h2></div>
          <div class="review-arrows">
            <button id="review-prev" aria-label="Previous review">←</button>
            <button id="review-next" aria-label="Next review">→</button>
          </div>
        </div>
        <div class="review-window">
          <div class="review-track" id="review-track">
            ${this.getReviewCards()}
          </div>
        </div>
      </section>

      <!-- Statement -->
      <section class="statement">
        <div class="statement-image"><img src="images/hero_banner.webp" alt="Motorcycle rider on the road" /></div>
        <div class="statement-copy">
          <p class="eyebrow red">The HRz standard</p>
          <h2>NOT JUST<br />A <em>RIDE.</em></h2>
          <p>Every curve, every downpour, every mile past midnight. The right gear means you can focus on what brought you here: the road in front of you.</p>
          <a href="#help" class="button button-outline">Our story <span>→</span></a>
          <div class="stat-row">
            <div><strong>12k+</strong><small>Riders equipped</small></div>
            <div><strong>4.9/5</strong><small>Rider rating</small></div>
          </div>
        </div>
      </section>

      <!-- New Drops -->
      <section class="new section" id="new">
        <div class="section-head">
          <div><p class="eyebrow red">Fresh off the truck</p><h2>NEW <em>DROPS</em></h2></div>
          <a href="#catalog" class="text-link">Shop new arrivals <span>→</span></a>
        </div>
        <div class="drop-grid">
          <article class="drop-card">
            <img src="images/category_helmets.webp" alt="Premium motorcycle helmet" />
            <div>
              <span class="drop-tag">NEW / HELMETS</span>
              <h3>Premium Series</h3>
              <a href="#helmets">Explore now →</a>
            </div>
          </article>
          <article class="drop-card">
            <img src="images/category_protection.webp" alt="Crash guard kit" />
            <div>
              <span class="drop-tag">NEW / PROTECTION</span>
              <h3>Guard Series</h3>
              <a href="#protection">Explore now →</a>
            </div>
          </article>
        </div>
      </section>

      <!-- Newsletter -->
      <section class="newsletter" id="journal">
        <p class="eyebrow red">Join the ride</p>
        <h2>ROAD NOTES,<br /><em>DELIVERED.</em></h2>
        <p>New gear, routes worth taking, and 10% off your first order.</p>
        <form id="newsletter-form">
          <input type="email" required placeholder="Your email address" aria-label="Your email address" />
          <button class="button button-red">Sign me up <span>→</span></button>
        </form>
        <small id="form-message"></small>
      </section>

      <!-- Service Strip -->
      <section class="service-strip">
        <div><b>✦</b><span><strong>Safe payments</strong><small>Cards · UPI · Wallets</small></span></div>
        <div><b>⌂</b><span><strong>Track your order</strong><small>Live delivery updates</small></span></div>
        <div><b>?</b><span><strong>Need help?</strong><small>Chat with a gear expert</small></span></div>
      </section>

      <!-- FAQ -->
      <section class="faq-section section">
        <p class="eyebrow red">Before you ride</p>
        <h2>QUICK <em>ANSWERS.</em></h2>
        <details><summary>How does the fitment guarantee work?</summary><p>When you select your bike from our dropdown, our catalog filters only items engineered for that model. If an item marked as compatible fails to fit, we issue a free return waybill and refund 100% of your money.</p></details>
        <details><summary>What are the shipping charges?</summary><p>Orders above ₹2,999 get FREE Express Shipping across India. Orders below ₹2,999 have a flat ₹199 delivery fee. Orders are dispatched within 24 hours.</p></details>
        <details><summary>Can I return gear?</summary><p>Yes. Unused gear can be returned within 7 days with a simple online return request. Fitment-related returns are always free.</p></details>
      </section>

      ${recentProducts.length ? `
      <!-- Recently Viewed -->
      <section class="recent section">
        <div class="section-head">
          <div><p class="eyebrow red">Keep exploring</p><h2>RECENTLY <em>VIEWED</em></h2></div>
        </div>
        <div class="product-grid" id="recent-product-grid">
          ${recentProducts.map(p => catalog.renderProductCard(p, activeBike, wishlist)).join("")}
        </div>
      </section>
      ` : ""}
    `;

    // Bind events
    catalog.bindCardEvents(container);

    // Home filter + sort state: the sort now applies to the currently
    // filtered set (previously it re-fetched the unfiltered 8 and
    // discarded the active filter).
    let currentHomeFilter = "all";
    let currentHomeSort = "featured";
    const renderHomeGrid = () => {
      const filtered = App.getHomeFilteredProducts(currentHomeFilter, activeBike, db);
      const sorted = App.homeSortProducts(filtered, currentHomeSort);
      const grid = container.querySelector("#home-product-grid");
      const count = container.querySelector("#product-count");
      if (grid) grid.innerHTML = sorted.map(p => catalog.renderProductCard(p, activeBike, wishlist)).join("");
      if (count) count.textContent = `${sorted.length} products`;
      catalog.bindCardEvents(container);
      App.syncWishlistBadge();
    };

    // Filter buttons (guarded: a missing Catalog.getDepartment no longer throws)
    container.querySelectorAll(".filters button").forEach(b => {
      b.onclick = () => {
        container.querySelector(".filters .active")?.classList.remove("active");
        b.classList.add("active");
        currentHomeFilter = b.dataset.filter || "all";
        renderHomeGrid();
      };
    });

    // Sort via the shared sorter (window.HRz.Catalog.sortProducts when
    // present, local fallback comparators otherwise), applied to the
    // currently filtered home set.
    const sortSelect = container.querySelector("#home-sort-select");
    if (sortSelect) {
      sortSelect.onchange = () => {
        currentHomeSort = sortSelect.value || "featured";
        renderHomeGrid();
      };
    }

    // Review carousel
    const reviewNext = container.querySelector("#review-next");
    const reviewPrev = container.querySelector("#review-prev");
    const reviewTrack = container.querySelector("#review-track");
    if (reviewNext && reviewTrack) {
      reviewNext.onclick = () => reviewTrack.append(reviewTrack.firstElementChild);
    }
    if (reviewPrev && reviewTrack) {
      reviewPrev.onclick = () => reviewTrack.prepend(reviewTrack.lastElementChild);
    }

    // Newsletter
    const nlForm = container.querySelector("#newsletter-form");
    if (nlForm) {
      nlForm.onsubmit = (e) => {
        e.preventDefault();
        e.currentTarget.reset();
        const msg = container.querySelector("#form-message");
        if (msg) msg.textContent = "You're on the list — welcome to the ride.";
        utils.showToast("Subscribed successfully!", "success");
      };
    }

    // ═══════════════════════════════════════════════════════════════
    //  3D Bike Selector — Glitch-Free Native CSS Snap + Infinite Loop
    // ═══════════════════════════════════════════════════════════════
    const sliderContainer = container.querySelector(".bike-slider-container");
    const bikeItems       = container.querySelectorAll(".bike-item");

    if (sliderContainer && bikeItems.length > 0) {
      const brands = Object.keys(window.HRz.Menu.menuData.shopByBike);
      const NUM_BIKES = brands.length; // Dynamic: 13 brands in catalog
      let filterTimer = null;
      let settleTimer = null;
      let lastActive = null;
      let rafScrollId = null;
      let autoScrollAnimId = null;

      // ─── Helpers ──────────────────────────────────────────────────
      const getScrollCenter = () => sliderContainer.scrollLeft + sliderContainer.clientWidth / 2;
      const getMid = (el) => el.offsetLeft + el.clientWidth / 2;

      const getClosestItem = () => {
        const center = getScrollCenter();
        let best = null, bestDist = Infinity;
        for (let i = 0; i < bikeItems.length; i++) {
          const el = bikeItems[i];
          const dist = Math.abs(getMid(el) - center);
          if (dist < bestDist) {
            bestDist = dist;
            best = el;
          }
        }
        return best;
      };

      const inferBikeCategory = (brand, model) => {
        const modelKey = String(model || "").toLowerCase();
        if (modelKey.includes("classic")) return "Classic";
        if (modelKey.includes("himalayan") || modelKey.includes("tiger") || modelKey.includes("gs")) return "Adventure";
        if (modelKey.includes("duke") || modelKey.includes("mt-15")) return "Naked";
        if (modelKey.includes("ninja") || modelKey.includes("r15") || modelKey.includes("panigale")) return "Supersport";
        return "Roadster";
      };

      const activateBike = (el, updateProducts = true) => {
        if (!el || el === lastActive) return;
        lastActive = el;
        bikeItems.forEach(i => i.classList.remove("active"));
        el.classList.add("active");

        if (!updateProducts) return;

        const brand = el.dataset.brand || el.querySelector("h3")?.innerText?.trim();
        if (!brand) return;
        const brandModels = window.HRz.Menu.menuData.shopByBike[brand] || [];
        const model = brandModels[0] || brand;
        const bikeObj = { brand, model, category: inferBikeCategory(brand, model) };

        clearTimeout(filterTimer);
        filterTimer = setTimeout(() => {
          const f = container.querySelector(".filters .active")?.dataset.filter || "all";
          const items = f === "all"
            ? db.getRecommendedProducts(bikeObj, null, 8)
            : db.getProductsForBike(bikeObj).filter(p => p.category === f);
          const grid  = container.querySelector("#home-product-grid");
          const count = container.querySelector("#product-count");
          if (grid)  grid.innerHTML = items.map(p => catalog.renderProductCard(p, bikeObj, wishlist)).join("");
          if (count) count.textContent = `${items.length} products`;
          catalog.bindCardEvents(container);
        }, 300);
      };

      // ─── Interaction & Intro Control ──────────────────────────────
      let isUserInteracting = false;
      let isDragging = false;
      let startX = 0, scrollLeftStart = 0, hasMoved = false;

      const cancelIntroAnimation = () => {
        if (sliderContainer.dataset.isAutoScrolling === "true") {
          if (autoScrollAnimId) {
            cancelAnimationFrame(autoScrollAnimId);
            autoScrollAnimId = null;
          }
          sliderContainer.dataset.isAutoScrolling = "false";
          sliderContainer.style.scrollSnapType = "";
          sliderContainer.style.pointerEvents = "";
        }
      };

      // ─── Touch Swiping Support ────────────────────────────────────
      let touchStartX = 0;
      let touchStartY = 0;
      let touchScrollStart = 0;

      sliderContainer.addEventListener("touchstart", (e) => {
        cancelIntroAnimation();
        clearTimeout(settleTimer);
        isUserInteracting = true;
        hasMoved = false;
        if (e.touches.length > 0) {
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
          touchScrollStart = sliderContainer.scrollLeft;
        }
      }, { passive: true });

      sliderContainer.addEventListener("touchmove", (e) => {
        cancelIntroAnimation();
        if (e.touches.length > 0) {
          const dx = e.touches[0].clientX - touchStartX;
          const dy = e.touches[0].clientY - touchStartY;
          // When gesture is horizontal, track finger 1:1 and disable snap during drag
          if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 6) {
            hasMoved = true;
            sliderContainer.style.scrollSnapType = "none";
            sliderContainer.scrollLeft = touchScrollStart - dx;
          }
        }
      }, { passive: true });

      const onTouchEnd = () => {
        isUserInteracting = false;
        sliderContainer.style.scrollSnapType = "";
        scheduleSettleCheck();
      };
      sliderContainer.addEventListener("touchend", onTouchEnd, { passive: true });
      sliderContainer.addEventListener("touchcancel", onTouchEnd, { passive: true });

      // ─── Wheel & Trackpad Support ─────────────────────────────────
      sliderContainer.addEventListener("wheel", () => {
        cancelIntroAnimation();
        scheduleSettleCheck();
      }, { passive: true });

      // ─── Desktop Drag Support ─────────────────────────────────────
      sliderContainer.addEventListener("mousedown", (e) => {
        if (e.button !== 0) return;
        cancelIntroAnimation();
        clearTimeout(settleTimer);
        isDragging = true;
        isUserInteracting = true;
        hasMoved = false;
        startX = e.clientX;
        scrollLeftStart = sliderContainer.scrollLeft;
        sliderContainer.style.scrollSnapType = "none";
        sliderContainer.style.cursor = "grabbing";
      });

      window.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        const walk = (e.clientX - startX) * 1.0;
        if (Math.abs(walk) > 8) hasMoved = true;
        sliderContainer.scrollLeft = scrollLeftStart - walk;
      });

      const onMouseUp = () => {
        if (!isDragging) return;
        isDragging = false;
        isUserInteracting = false;
        sliderContainer.style.cursor = "grab";
        sliderContainer.style.scrollSnapType = "";
        scheduleSettleCheck();
      };
      window.addEventListener("mouseup", onMouseUp);

      // ─── Click / Tap Handling ─────────────────────────────────────
      sliderContainer.addEventListener("click", (e) => {
        if (hasMoved) {
          e.preventDefault();
          e.stopPropagation();
          return; // Was a swipe/drag, do not navigate
        }
        const clicked = e.target.closest(".bike-item");
        if (!clicked) return;
        const brandName = clicked.dataset.brand || clicked.querySelector("h3")?.innerText?.trim();
        if (!brandName) return;

        if (clicked.classList.contains("active")) {
          window.location.hash = "#models?brand=" + encodeURIComponent(brandName);
        } else {
          const targetPos = getMid(clicked) - sliderContainer.clientWidth / 2;
          sliderContainer.scrollTo({ left: targetPos, behavior: "smooth" });
          activateBike(clicked);
        }
      });
      sliderContainer.addEventListener("dragstart", (e) => e.preventDefault());

      // ─── Active Card Sync on Scroll (RAF-throttled) ────────────────
      sliderContainer.addEventListener("scroll", () => {
        if (sliderContainer.dataset.isAutoScrolling === "true") return;

        if (!rafScrollId) {
          rafScrollId = requestAnimationFrame(() => {
            rafScrollId = null;
            const closest = getClosestItem();
            if (closest && closest !== lastActive) {
              activateBike(closest);
            }
          });
        }

        scheduleSettleCheck();
      }, { passive: true });

      // ─── Glitch-Free Infinite Normalization ────────────────────────
      const checkAndNormalizeLoop = () => {
        // Never jump or normalize while user is actively touching or dragging!
        if (isUserInteracting || isDragging || sliderContainer.dataset.isAutoScrolling === "true") {
          return;
        }

        const currentClosest = getClosestItem();
        if (!currentClosest) return;
        const idx = Array.from(bikeItems).indexOf(currentClosest);
        if (idx === -1) return;

        // Middle set is [NUM_BIKES ... 2 * NUM_BIKES - 1] (indices 13 to 25)
        if (idx < NUM_BIKES || idx >= NUM_BIKES * 2) {
          const middleIdx = (idx % NUM_BIKES) + NUM_BIKES;
          const targetEl = bikeItems[middleIdx];
          if (!targetEl) return;

          const targetPos = getMid(targetEl) - sliderContainer.clientWidth / 2;

          // Seamless instant reposition
          sliderContainer.style.scrollSnapType = "none";
          sliderContainer.scrollLeft = targetPos;

          lastActive = targetEl;
          bikeItems.forEach(i => i.classList.remove("active"));
          targetEl.classList.add("active");

          requestAnimationFrame(() => {
            sliderContainer.style.scrollSnapType = "";
          });
        }
      };

      const scheduleSettleCheck = () => {
        clearTimeout(settleTimer);
        // If native scrollend is supported, let it handle the settle check reliably
        // Otherwise fallback to 400ms idle timer to avoid interrupting momentum scroll
        if (!("onscrollend" in window)) {
          settleTimer = setTimeout(checkAndNormalizeLoop, 400);
        }
      };

      if ("onscrollend" in window) {
        sliderContainer.addEventListener("scrollend", checkAndNormalizeLoop, { passive: true });
      }

      // ─── Initial Center & Intro Showcase Animation ────────────────
      const middleStartEl = bikeItems[NUM_BIKES]; // Royal Enfield (start of middle set)
      const middleEndEl = bikeItems[NUM_BIKES + 3]; // Triumph (3 brands ahead in middle set)

      if (middleStartEl) {
        // Position immediately at the canonical middle set
        sliderContainer.scrollLeft = getMid(middleStartEl) - sliderContainer.clientWidth / 2;
        activateBike(middleStartEl, false);
      }

      if (middleStartEl && middleEndEl) {
        const observer = new IntersectionObserver((entries) => {
          if (entries[0].isIntersecting) {
            observer.disconnect();
            if (isUserInteracting || hasMoved) return;

            sliderContainer.dataset.isAutoScrolling = "true";
            sliderContainer.style.scrollSnapType = "none";

            const duration = 1800;
            const startTime = performance.now();
            const startPos = getMid(middleStartEl) - sliderContainer.clientWidth / 2;
            const endPos = getMid(middleEndEl) - sliderContainer.clientWidth / 2;

            const animateScroll = (time) => {
              if (sliderContainer.dataset.isAutoScrolling !== "true") return; // User touched or swiped!
              const elapsed = time - startTime;
              const progress = Math.min(elapsed / duration, 1);
              // Smooth cubic ease-out
              const ease = 1 - Math.pow(1 - progress, 3);
              sliderContainer.scrollLeft = startPos + (endPos - startPos) * ease;

              const current = getClosestItem();
              if (current && current !== lastActive) {
                lastActive = current;
                bikeItems.forEach(b => b.classList.remove("active"));
                current.classList.add("active");
              }

              if (progress < 1) {
                autoScrollAnimId = requestAnimationFrame(animateScroll);
              } else {
                sliderContainer.dataset.isAutoScrolling = "false";
                sliderContainer.style.scrollSnapType = "";
                activateBike(middleEndEl);
              }
            };

            autoScrollAnimId = requestAnimationFrame(animateScroll);
          }
        }, { threshold: 0.3 });

        observer.observe(sliderContainer);
      }

      // ─── Prev / Next Button Navigation ────────────────────────────
      const prevBtn = container.querySelector("#bikeSliderPrev");
      const nextBtn = container.querySelector("#bikeSliderNext");
      if (prevBtn) {
        prevBtn.addEventListener("click", (e) => {
          e.preventDefault();
          cancelIntroAnimation();
          const cardWidth = bikeItems[0]?.offsetWidth || 180;
          sliderContainer.scrollBy({ left: -(cardWidth + 30), behavior: "smooth" });
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener("click", (e) => {
          e.preventDefault();
          cancelIntroAnimation();
          const cardWidth = bikeItems[0]?.offsetWidth || 180;
          sliderContainer.scrollBy({ left: (cardWidth + 30), behavior: "smooth" });
        });
      }
    }
    // ═══════════════════════════════════════════════════════════════
  }

  static getReviewCards() {
    const reviews = window.HRz.DB.getReviews ? window.HRz.DB.getReviews().filter(r => r.status === "published").slice(0, 6) : [];
    const escapeHTML = window.HRz.Utils.escapeHTML;
    if (reviews.length > 0) {
      return reviews.map(r => `
        <article class="review-card">
          <div class="stars">★★★★★</div>
          <blockquote>"${escapeHTML(r.comment)}"</blockquote>
          <div class="reviewer">
            <span>${escapeHTML(r.reviewerName.split(" ").map(n => n[0]).join(""))}</span>
            <p><b>${escapeHTML(r.reviewerName)}</b><small>Verified rider · ${escapeHTML(r.bikeName || "India")}</small></p>
          </div>
        </article>
      `).join("");
    }
    // Fallback review cards
    return `
      <article class="review-card">
        <div class="stars">★★★★★</div>
        <blockquote>"Finally, gear that feels as good on the fifth hour as it does when you roll out."</blockquote>
        <div class="reviewer"><span>JM</span><p><b>Jai Malhotra</b><small>Verified rider · Pune</small></p></div>
      </article>
      <article class="review-card">
        <div class="stars">★★★★★</div>
        <blockquote>"The crash guard fitted perfectly on my Himalayan. Zero modifications needed."</blockquote>
        <div class="reviewer"><span>AK</span><p><b>Amar Kapoor</b><small>Verified rider · Delhi</small></p></div>
      </article>
      <article class="review-card">
        <div class="stars">★★★★★</div>
        <blockquote>"Clean site, serious kit, fast delivery. This is now my go-to for every upgrade."</blockquote>
        <div class="reviewer"><span>RS</span><p><b>Riya Shah</b><small>Verified rider · Mumbai</small></p></div>
      </article>
    `;
  }

  static renderWishlistView(container) {
    const wishlistIds = window.HRz.Storage.getWishlist();
    const activeBike = window.HRz.Storage.getActiveBike();
    const products = window.HRz.DB.getProducts().filter(p => wishlistIds.includes(p.id));
    const catalog = window.HRz.Catalog;

    container.innerHTML = `
      <div class="breadcrumb-trail">
        <a href="#home">Home</a> / <span class="current">My Wishlist</span>
      </div>
      <div class="view-header">
        <div>
          <p class="eyebrow red">Saved Items</p>
          <h2>MY <em>WISHLIST</em> (${products.length})</h2>
        </div>
      </div>
      ${products.length === 0 ? `
        <div class="empty-state-card">
          <div class="empty-icon">❤️</div>
          <h3>Your Wishlist is Empty</h3>
          <p>Tap the heart icon on any product to save it to your wishlist for later.</p>
          <button class="accent-button" onclick="window.location.hash='catalog'">Explore Products</button>
        </div>
      ` : `
        <div class="product-grid inner-section">
          ${products.map(p => catalog.renderProductCard(p, activeBike, wishlistIds)).join("")}
        </div>
      `}
    `;
    catalog.bindCardEvents(container);
    this.syncWishlistBadge();
  }

  static getOrderStatusClass(status) {
    if (!status) return "";
    const lower = status.toLowerCase();
    if (lower.includes("placed")) return "placed";
    // "Pending WhatsApp Confirmation" is an order received but not yet
    // confirmed — it sits at the Ordered step (0% progress).
    if (lower.includes("pending")) return "placed";
    // "Confirmed" means processing has started.
    if (lower.includes("confirm")) return "processing";
    if (lower.includes("processing")) return "processing";
    if (lower.includes("shipped") || lower.includes("transit")) return "shipped";
    if (lower.includes("delivered")) return "delivered";
    if (lower.includes("cancelled")) return "cancelled";
    return "";
  }

  static getOrderTimelineHTML(status) {
    const sClass = this.getOrderStatusClass(status);
    let progress = 0;
    
    // Ordered is always complete unless cancelled before even ordered? No, cancelled is after ordered.
    let procClass = "", shipClass = "", delivClass = "";
    
    if (sClass === "cancelled") {
      return `
        <div class="order-timeline-wrapper">
          <div class="order-timeline" style="max-width: 300px;">
            <div class="order-timeline-progress" style="width: 100%; background: #f44336;"></div>
            
            <div class="timeline-step completed">
              <div class="step-icon">✓</div>
              <div class="step-label">Ordered</div>
            </div>
            
            <div class="timeline-step active" style="margin-left: auto;">
              <div class="step-icon" style="background: #f44336; border-color: #f44336;">✕</div>
              <div class="step-label" style="color: #f44336;">Cancelled</div>
            </div>
          </div>
        </div>
      `;
    }
    
    if (sClass === "processing") {
      progress = 33;
      procClass = "active";
    } else if (sClass === "shipped") {
      progress = 66;
      procClass = "completed";
      shipClass = "active";
    } else if (sClass === "delivered") {
      progress = 100;
      procClass = "completed";
      shipClass = "completed";
      delivClass = "active";
    }
    // if placed, progress = 0, no extra classes

    return `
      <div class="order-timeline-wrapper">
        <div class="order-timeline">
          <div class="order-timeline-progress" style="width: ${progress}%;"></div>
          
          <div class="timeline-step completed">
            <div class="step-icon">✓</div>
            <div class="step-label">Ordered</div>
          </div>
          
          <div class="timeline-step ${procClass}">
            <div class="step-icon">${procClass === 'completed' ? '✓' : '⚙'}</div>
            <div class="step-label">Processing</div>
          </div>
          
          <div class="timeline-step ${shipClass}">
            <div class="step-icon">${shipClass === 'completed' ? '✓' : '🚚'}</div>
            <div class="step-label">Shipped</div>
          </div>
          
          <div class="timeline-step ${delivClass}">
            <div class="step-icon">${delivClass === 'completed' || delivClass === 'active' ? '✓' : '📦'}</div>
            <div class="step-label">Delivered</div>
          </div>
        </div>
      </div>
    `;
  }

  static renderTrackingView(container) {
    const orders = window.HRz.DB.getOrders();
    const utils = window.HRz.Utils;
    const escapeHTML = utils.escapeHTML;

    container.innerHTML = `
      <div class="breadcrumb-trail">
        <a href="#home">Home</a> / <span class="current">My Orders</span>
      </div>
      <div class="view-header">
        <div>
          <p class="eyebrow red">Order History & Track Waybill</p>
          <h2>MY <em>ORDERS</em></h2>
        </div>
      </div>
      ${orders.length === 0 ? `
        <div class="empty-state-card">
          <div class="empty-icon">📦</div>
          <h3>No Orders Found</h3>
          <p>When you place an order, your tracking updates and fitment records will appear here.</p>
        </div>
      ` : `
        <div class="orders-history-list">
          ${orders.map(o => {
            const firstItem = o.items[0];
            const badgeClass = this.getOrderStatusClass(o.status);
            
            return `
              <div class="order-card" onclick="window.HRz.App.openOrderDetailsModal('${escapeHTML(o.id)}')">
                <div class="order-card-header">
                  <div>
                    <strong>Order ID: ${escapeHTML(o.id)}</strong>
                    <small>Placed on ${escapeHTML(o.date)}</small>
                  </div>
                  <span class="order-status-badge ${badgeClass}">${escapeHTML(o.status)}</span>
                </div>
                
                <div class="order-card-body">
                  <div class="order-items-preview-row">
                    ${o.items.map(i => `
                      <img src="${escapeHTML(i.image || 'images/helmet_product.webp')}" alt="${escapeHTML(i.name)}" class="order-item-thumb" onerror="this.src='images/helmet_product.webp'" />
                    `).join("")}
                    <div class="order-item-details-compact">
                      <strong>${escapeHTML(firstItem ? firstItem.name : "Accessories")}</strong>
                      <small>${o.items.length > 1 ? `+ ${o.items.length - 1} more items` : "1 item"}</small>
                    </div>
                  </div>
                  
                  ${this.getOrderTimelineHTML(o.status)}
                </div>
                
                <div class="order-card-footer">
                  <span>Tracking: <code>${escapeHTML(o.trackingId)}</code></span>
                  <strong>${utils.formatCurrency(o.total)} <small style="font-size:14px; font-weight:normal;">→</small></strong>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      `}
    `;
  }

  static openOrderDetailsModal(orderId) {
    const order = window.HRz.DB.getOrders().find(o => o.id === orderId);
    if (!order) return;

    let modal = document.getElementById("orderDetailsModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "orderDetailsModal";
      modal.className = "order-details-modal";
      document.body.appendChild(modal);
    }

    const utils = window.HRz.Utils;
    const escapeHTML = utils.escapeHTML;
    
    // Calculate progress for modal timeline
    const sClass = this.getOrderStatusClass(order.status);
    let progress = 0;
    let procClass = "", shipClass = "", delivClass = "";
    
    let timelineHTML = "";

    if (sClass === "cancelled") {
      timelineHTML = `
        <div class="modal-timeline-wrapper">
          <div class="modal-timeline">
            <div class="modal-timeline-progress" style="height: 100%; background: #f44336;"></div>
            
            <div class="modal-timeline-step completed">
              <div class="step-icon">✓</div>
              <div class="step-content">
                <strong>Order Placed</strong>
                <small>We received your order.</small>
              </div>
            </div>
            
            <div class="modal-timeline-step active">
              <div class="step-icon" style="background: #f44336; border-color: #f44336;">✕</div>
              <div class="step-content">
                <strong style="color: #f44336;">Cancelled</strong>
                <small>This order has been cancelled.</small>
              </div>
            </div>
          </div>
        </div>
      `;
    } else {
      if (sClass === "processing") {
        progress = 33;
        procClass = "active";
      } else if (sClass === "shipped") {
        progress = 66;
        procClass = "completed";
        shipClass = "active";
      } else if (sClass === "delivered") {
        progress = 100;
        procClass = "completed";
        shipClass = "completed";
        delivClass = "active";
      }

      timelineHTML = `
        <div class="modal-timeline-wrapper">
          <div class="modal-timeline">
            <div class="modal-timeline-progress" style="height: ${progress}%;"></div>
            
            <div class="modal-timeline-step completed">
              <div class="step-icon">✓</div>
              <div class="step-content">
                <strong>Order Placed</strong>
                <small>We've received your order.</small>
              </div>
            </div>
            
            <div class="modal-timeline-step ${procClass}">
              <div class="step-icon">${procClass === 'completed' ? '✓' : '⚙'}</div>
              <div class="step-content">
                <strong>Processing</strong>
                <small>Verifying fitment & packing.</small>
              </div>
            </div>
            
            <div class="modal-timeline-step ${shipClass}">
              <div class="step-icon">${shipClass === 'completed' ? '✓' : '🚚'}</div>
              <div class="step-content">
                <strong>Shipped</strong>
                <small>Handed over to courier partner.</small>
              </div>
            </div>
            
            <div class="modal-timeline-step ${delivClass}">
              <div class="step-icon">${delivClass === 'completed' || delivClass === 'active' ? '✓' : '📦'}</div>
              <div class="step-content">
                <strong>Delivered</strong>
                <small>Enjoy the ride.</small>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    modal.innerHTML = `
      <div class="order-details-header">
        <h2>Order Details</h2>
        <button class="order-details-close" id="closeOrderModalBtn" aria-label="Close modal">×</button>
      </div>
      
      <div class="order-details-content">
        <div class="order-details-main">
          
          <div class="order-section-card">
            <h3>Items Ordered</h3>
            <div class="full-order-items-list">
              ${order.items.map(item => `
                <div class="full-order-item">
                  <img src="${escapeHTML(item.image || 'images/helmet_product.webp')}" alt="${escapeHTML(item.name)}" onerror="this.src='images/helmet_product.webp'" />
                  <div class="full-order-item-info">
                    <strong>${escapeHTML(item.name)}</strong>
                    <small>Qty: ${item.quantity} · SKU: ${escapeHTML(item.sku || 'N/A')}</small>
                  </div>
                  <div class="full-order-item-price">
                    ${utils.formatCurrency(item.price * item.quantity)}
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
          
          <div class="order-section-card">
            <h3>Order Information</h3>
            <div class="order-info-grid">
              <div class="info-block">
                <span>Order ID</span>
                <strong>${escapeHTML(order.id)}</strong>
              </div>
              <div class="info-block">
                <span>Order Date</span>
                <strong>${escapeHTML(order.date)}</strong>
              </div>
              <div class="info-block">
                <span>Payment Method</span>
                <strong>${escapeHTML(order.paymentMethod || 'Prepaid')}</strong>
              </div>
              <div class="info-block">
                <span>Shipping Address</span>
                <strong>${escapeHTML(order.shippingAddress || 'Address details not available')}</strong>
              </div>
              <div class="info-block">
                <span>Bike Fitment Verified</span>
                <strong>${escapeHTML(order.bike)}</strong>
              </div>
            </div>
          </div>
          
        </div>
        
        <div class="order-details-sidebar">
          
          <div class="order-section-card">
            <h3>Tracking & Status</h3>
            <div class="info-block" style="margin-bottom:16px;">
              <span>Waybill / Tracking ID</span>
              <strong style="font-family:'DM Mono', monospace; font-size:16px; background:rgba(255,255,255,0.05); padding:8px; border-radius:4px; display:block;">${escapeHTML(order.trackingId)}</strong>
            </div>
            
            ${timelineHTML}
          </div>
          
          <div class="order-section-card">
            <h3>Summary</h3>
            <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
              <span style="color:var(--mute);">Subtotal</span>
              <span>${utils.formatCurrency(order.total)}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:16px; padding-bottom:16px; border-bottom:1px solid var(--border);">
              <span style="color:var(--mute);">Shipping</span>
              <span style="color:#81c784;">Free</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
              <strong>Grand Total</strong>
              <strong style="font-size:20px;">${utils.formatCurrency(order.total)}</strong>
            </div>
          </div>
          
        </div>
      </div>
    `;

    // Add close events
    const closeBtn = modal.querySelector("#closeOrderModalBtn");
    if (closeBtn) {
      closeBtn.onclick = () => this.closeOrderDetailsModal();
    }
    
    // Add escape key support
    this._orderModalKeyHandler = (e) => {
      if (e.key === "Escape") this.closeOrderDetailsModal();
    };
    document.addEventListener("keydown", this._orderModalKeyHandler);

    // Open animation
    // Force reflow
    void modal.offsetWidth; 
    modal.classList.add("open");
    document.body.style.overflow = "hidden"; // Prevent background scrolling
    
    if (!window.history.state || !window.history.state.orderModalOpen) {
      window.history.pushState({ orderModalOpen: true }, "");
    }
  }

  static closeOrderDetailsModal(isPopState = false, skipHistory = false) {
    const modal = document.getElementById("orderDetailsModal");
    if (!modal) return;
    
    const wasOpen = modal.classList.contains("open");
    modal.classList.remove("open");
    document.body.style.overflow = "";
    
    if (this._orderModalKeyHandler) {
      document.removeEventListener("keydown", this._orderModalKeyHandler);
      this._orderModalKeyHandler = null;
    }

    if (wasOpen && !isPopState && window.history.state && window.history.state.orderModalOpen) {
      if (!skipHistory) {
        window.history.back();
      } else {
        window.history.replaceState({}, "");
      }
    }
  }

  static renderReviewsView(container) {
    const reviews = window.HRz.DB.getReviews().filter(r => r.status === "published");
    const utils = window.HRz.Utils;
    const escapeHTML = utils.escapeHTML;

    container.innerHTML = `
      <div class="breadcrumb-trail">
        <a href="#home">Home</a> / <span class="current">Reviews</span>
      </div>
      <div class="view-header">
        <div>
          <p class="eyebrow red">Rider Community Feedback</p>
          <h2>VERIFIED RIDER <em>REVIEWS</em></h2>
        </div>
      </div>
      <div class="inner-section">
        ${reviews.map(r => `
          <div class="review-card">
            <div class="review-header">
              <span class="reviewer-name"><b>${escapeHTML(r.reviewerName)}</b></span>
              <span class="review-bike-tag">Verified ${escapeHTML(r.bikeName)}</span>
              <span class="review-date">${escapeHTML(r.date)}</span>
            </div>
            <div class="review-rating">${utils.renderStarRating(r.rating)}</div>
            <h4 class="review-title">${escapeHTML(r.title)}</h4>
            <p class="review-comment" style="color:var(--mute); margin-top:8px;">${escapeHTML(r.comment)}</p>
          </div>
        `).join("")}
      </div>
    `;
  }

  static renderHelpView(container) {
    container.innerHTML = `
      <div class="breadcrumb-trail">
        <a href="#home">Home</a> / <span class="current">FAQ & Support</span>
      </div>
      <div class="view-header">
        <div>
          <p class="eyebrow red">Help & Support Center</p>
          <h2>QUICK <em>ANSWERS</em></h2>
        </div>
      </div>
      <div class="faq-section inner-section">
        <details>
          <summary>How does the 100% Fitment Guarantee work?</summary>
          <p>When you select your bike from our dropdown (Make, Model, Year, Variant), our catalog filters only items engineered for that model. If an item marked as compatible fails to fit, we issue a free return waybill and refund 100% of your money.</p>
        </details>
        <details>
          <summary>What are the shipping charges and timeline?</summary>
          <p>Orders above ₹2,999 get FREE Express Shipping across India. Orders below ₹2,999 have a flat ₹199 delivery fee. Orders are dispatched within 24 hours.</p>
        </details>
        <details>
          <summary>How do I report a part that didn't fit?</summary>
          <p>Go to the product page or your account order history and click "Didn't Fit My Bike?". Fill out the brief report form and our team will issue an immediate return label.</p>
        </details>
        <details>
          <summary>What payment methods do you accept?</summary>
          <p>We accept UPI (GPay, PhonePe, Paytm), all major credit and debit cards (Visa, Mastercard, RuPay, Amex), and Cash on Delivery (COD).</p>
        </details>
        <details>
          <summary>Do you ship internationally?</summary>
          <p>Currently we ship PAN-India only. International shipping is planned for Q4 2026. Sign up for our newsletter to be notified.</p>
        </details>

          <h3 style="margin-top: 48px; margin-bottom: 24px; font-family: var(--font-display); text-transform: uppercase;">Legal & Policies</h3>
          
          <details>
            <summary>Terms & Conditions</summary>
            <p>Welcome to HRz Pitstop. By using our website, you agree to these terms. All content is for informational purposes. Product specifications are subject to change without notice. We reserve the right to refuse service, terminate accounts, or cancel orders at our discretion. Our full terms govern your use of our platform.</p>
          </details>
          
          <details>
            <summary>Privacy Policy</summary>
            <p>We value your privacy. HRz Pitstop collects personal information such as your name, email, and shipping address solely for fulfilling your orders. We do not sell your data to third parties. Our site uses secure encryption to protect your information. For more details, contact our support team.</p>
          </details>
          
          <details>
            <summary>Return & Refund Policy</summary>
            <p>We offer a 7-Day Free Fitment Return Guarantee. If the product does not fit your vehicle despite being marked as compatible, you may return it within 7 days for a full refund. The item must be unused, in its original packaging, and with all tags attached. Refunds are processed to the original payment method within 5-7 business days after we receive the return.</p>
          </details>
        </div>
      `;
  }

  static renderModelsView(container, brand) {
    if (!brand) {
      window.location.hash = "#home";
      return;
    }
    const models = window.HRz.Menu.menuData.shopByBike[brand] || [];
    
    container.innerHTML = `
      <div class="section-head" style="margin-top:40px; text-align:center;">
        <div><p class="eyebrow red">${brand}</p><h2>SELECT YOUR <em>MODEL</em></h2></div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 24px; padding: 40px 4vw;">
        ${models.map((model, idx) => {
          const fallbackUrl = (window.HRzImageMap && window.HRzImageMap[brand]) || `images/verified bikes/bike_images/${brand}.png`;
          const imgUrl = (window.HRzImageMap && window.HRzImageMap[model]) || fallbackUrl;
          return `
          <div style="cursor:pointer; background: #111215; border-radius: 16px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.05); transition: transform 0.3s ease, box-shadow 0.3s ease;" 
               onclick="window.location.hash='#catalog?search=' + encodeURIComponent('${model}')"
               onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.4)'"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
            <div style="padding: 20px; background: transparent; display: flex; align-items: center; justify-content: center; height: 180px;">
              <img src="${imgUrl}" alt="${model}" style="max-height: 120%; max-width: 120%; object-fit: contain; filter: drop-shadow(0 6px 12px rgba(0,0,0,0.25));" onerror="this.onerror=null; this.src='${fallbackUrl}'" />
            </div>
            <div style="padding: 16px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.05);">
              <h3 style="margin: 0; font-size: 16px; color: #ffffff; font-weight: 700; text-transform: uppercase;">${model}</h3>
            </div>
          </div>
        `}).join('')}
      </div>
    `;
  }
}

window.HRz.App = App;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => App.init());
} else {
  App.init();
}














