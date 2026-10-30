/* =============================================
   HRz PITSTOP – Shopping Cart Drawer & Shipping Progress Module
   Adapted for editorial design drawer
   ============================================= */

window.HRz = window.HRz || {};

const FREE_SHIPPING_THRESHOLD = 2999;

class CartDrawer {
  static init() {
    this.bindEvents();
    this.updateCartBadge();
  }

  static bindEvents() {
    const openBtn = document.getElementById("openCartBtn");
    const closeBtn = document.getElementById("closeCartBtn");
    const overlay = document.getElementById("overlay");

    if (openBtn) openBtn.onclick = () => this.openCart();
    if (closeBtn) closeBtn.onclick = () => this.closeCart();

    window.addEventListener("hrz:add-to-cart", (e) => {
      const product = e.detail.product;
      const quantity = e.detail.quantity;
      if (this._loginGatePassed()) {
        this.addItem(product, quantity ? { quantity } : {});
      } else {
        this._promptForLogin(
          () => {
            this.addItem(product, quantity ? { quantity } : {});
          },
          () => {
            window.HRz.Utils.showToast("Sign in or guest mode required to add items", "info");
          }
        );
      }
    });

    // Shared BUY NOW path: any quick-view or other surface dispatches
    // "hrz:buy-now" instead of re-implementing add + navigate logic.
    window.addEventListener("hrz:buy-now", (e) => {
      if (e.detail && e.detail.product) this.buyNow(e.detail.product);
    });
  }

  // True when the visitor is signed in OR has already made a durable
  // guest/login-prompt choice (persisted in localStorage via Storage, so
  // it survives reloads — the old in-memory-only flag did not).
  static _loginGatePassed() {
    try {
      if (window.HRz.Auth && window.HRz.Auth.isLoggedIn()) return true;
    } catch (e) { /* fall through to the persisted choice */ }
    if (this.add_to_bag_login_prompted === true) return true;
    try {
      if (window.HRz.Storage && typeof window.HRz.Storage.hasLoginPrompted === "function") {
        return window.HRz.Storage.hasLoginPrompted();
      }
    } catch (e) { /* fall through */ }
    return false;
  }

  // Persist the guest/login-prompt choice BEFORE showing the popup, so
  // dismissing it (or reloading) does not re-prompt on the next add.
  // The item from the dismissed attempt itself is still not added; the
  // next add succeeds without another prompt.
  static _markLoginPrompted() {
    this.add_to_bag_login_prompted = true;
    try {
      if (window.HRz.Storage && typeof window.HRz.Storage.setLoginPrompted === "function") {
        window.HRz.Storage.setLoginPrompted(true);
      }
    } catch (e) { /* in-memory flag above still applies this session */ }
  }

  static _promptForLogin(onSuccess, onCancel) {
    this._markLoginPrompted();
    if (window.HRz.Auth && typeof window.HRz.Auth.showLoginPopup === "function") {
      window.HRz.Auth.showLoginPopup(onSuccess, onCancel);
    } else if (typeof onSuccess === "function") {
      onSuccess();
    }
  }

  // Dedupe key: base product id + variant (colour) + size. Variant-colour
  // or size suffixed ids must not clobber different sizes or colors.
  static _cartItemKey(item) {
    const variant = item.color || item.variant || item.variantName || "";
    const slug = String(variant).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    let base = item.id || "";
    if (slug && base.endsWith("-" + slug)) base = base.slice(0, -(slug.length + 1));
    const size = item.selectedSize || item.size || "";
    const sizeSlug = String(size).toLowerCase().replace(/[^a-z0-9]+/g, "");
    if (sizeSlug && base.includes("-size-" + sizeSlug)) {
      base = base.replace("-size-" + sizeSlug, "");
    }
    return base + "||" + slug + (sizeSlug ? "||" + sizeSlug : "");
  }

  // THE single BUY NOW path (product page and any catalog quick-view):
  // add (or increment) exactly once, never open the cart drawer, close
  // any drawer that is already open, then go to checkout. No timer:
  // setCart is synchronous, so there is nothing to wait 100ms for.
  static buyNow(product, options = {}) {
    const proceed = () => {
      this.addItem(product, { suppressDrawer: true, ...(options.quantity ? { quantity: options.quantity } : {}) });
      this.closeCart(false, true);
      window.location.hash = "checkout";
    };
    if (this._loginGatePassed()) {
      proceed();
    } else {
      // Dismissing the popup adds nothing and navigates nowhere.
      this._promptForLogin(proceed, null);
    }
  }

  static openCart() {
    this._openCartDrawer();
  }

  static _openCartDrawer() {
    const drawer = document.getElementById("cartDrawer");
    const overlay = document.getElementById("overlay");
    if (drawer) {
      drawer.classList.add("open");
      if (overlay) overlay.classList.add("open");
      this.renderCartItems();
      
      if (!window.history.state || !window.history.state.panelOpen) {
        window.history.pushState({ panelOpen: true }, "");
      }
    }
  }

  static closeCart(isPopState = false, skipHistory = false) {
    const drawer = document.getElementById("cartDrawer");
    const overlay = document.getElementById("overlay");
    const wasOpen = drawer && drawer.classList.contains("open");
    if (drawer) drawer.classList.remove("open");
    if (overlay) overlay.classList.remove("open");
    
    if (wasOpen && !isPopState && window.history.state && window.history.state.panelOpen) {
      if (!skipHistory) {
        window.history.back();
      } else {
        window.history.replaceState({}, "");
      }
    }
  }

  static addItem(product, options = {}) {
    const cart = window.HRz.Storage.getCart();
    const isFirstItem = cart.length === 0;
    const qtyToAdd = Math.max(1, Number(options.quantity) || 1);
    // Match by composite key: id + variant + size
    const key = this._cartItemKey(product);
    const existing = cart.find(item => item.id === product.id || this._cartItemKey(item) === key);

    if (existing) {
      existing.quantity += qtyToAdd;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        sku: product.sku,
        // Preserve the variant and size so they survive a reload.
        ...(product.color ? { color: product.color } : {}),
        ...(product.variant ? { variant: product.variant } : {}),
        ...(product.selectedSize ? { selectedSize: product.selectedSize } : (product.size ? { selectedSize: product.size } : {})),
        quantity: qtyToAdd
      });
    }

    window.HRz.Storage.setCart(cart);
    this.updateCartBadge();

    if (isFirstItem && !options.suppressDrawer) {
      this.openCart();
    }

    const colorText = product.color ? ` (Color: ${product.color})` : "";
    const sizeText = product.selectedSize ? ` [Size: ${product.selectedSize}]` : "";
    window.HRz.Utils.showToast(`Added ${product.name}${colorText}${sizeText} to bag`, "success");
  }

  static updateQuantity(productId, delta) {
    let cart = window.HRz.Storage.getCart();
    const existing = cart.find(item => item.id === productId);

    if (existing) {
      existing.quantity += delta;
      if (existing.quantity <= 0) {
        cart = cart.filter(item => item.id !== productId);
      }
    }

    window.HRz.Storage.setCart(cart);
    this.updateCartBadge();
    this.renderCartItems();
  }

  static updateCartBadge() {
    // A missing badge element (or missing Storage) must never throw.
    try {
      const cart = (window.HRz.Storage && typeof window.HRz.Storage.getCart === "function")
        ? window.HRz.Storage.getCart()
        : [];
      const totalCount = cart.reduce((sum, i) => sum + (Number(i.quantity) || 0), 0);

      // Update all badge locations, if present
      const badge = document.getElementById("cartCountBadge");
      if (badge) badge.textContent = totalCount;

      const drawerCount = document.getElementById("drawerCount");
      if (drawerCount) drawerCount.textContent = totalCount;

      const mobileCount = document.getElementById("mobileCartCount");
      if (mobileCount) mobileCount.textContent = totalCount;
    } catch (e) {
      /* Badge update is cosmetic; never break add-to-cart/checkout. */
    }
  }

  static renderCartItems() {
    const cart = window.HRz.Storage.getCart();
    const container = document.getElementById("cartDrawerItems");
    const subtotal = cart.reduce((sum, i) => sum + (i.price * i.quantity), 0);
    const utils = window.HRz.Utils;
    const escapeHTML = utils.escapeHTML;

    const progressText = document.getElementById("shippingProgressText");
    const progressBar = document.getElementById("shippingProgressBar");

    if (progressText && progressBar) {
      if (subtotal >= FREE_SHIPPING_THRESHOLD) {
        progressText.innerHTML = `🎉 You've unlocked <strong>FREE PAN-India Express Shipping!</strong>`;
        progressBar.style.width = "100%";
      } else {
        const remaining = FREE_SHIPPING_THRESHOLD - subtotal;
        const pct = Math.min(100, Math.round((subtotal / FREE_SHIPPING_THRESHOLD) * 100));
        progressText.innerHTML = `Add <strong>${utils.formatCurrency(remaining)}</strong> more for FREE Shipping!`;
        progressBar.style.width = `${pct}%`;
      }
    }

    if (!container) return;

    if (cart.length === 0) {
      container.innerHTML = `<p class="empty-state">Your bag is ready when you are.</p>
        <div class="cart-drawer-actions">
          <button class="text-button cart-continue-btn">Continue shopping →</button>
        </div>`;
    } else {
      container.innerHTML = cart.map(item => `
        <div class="cart-item-row">
          <img src="${escapeHTML(item.image)}" alt="${escapeHTML(item.name)}" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
          <div class="cart-item-info">
            <small class="cart-item-sku">${escapeHTML(item.sku || "Accessory")}</small>
            <h4 class="cart-item-title">${escapeHTML(item.name)}</h4>
            <div class="cart-item-variants-row" style="display:flex; flex-wrap:wrap; gap:4px; margin:2px 0 4px 0;">
              ${item.color ? `<span class="cart-item-color-pill">Color: <strong>${escapeHTML(item.color)}</strong></span>` : ""}
              ${item.selectedSize ? `<span class="cart-item-size-pill">Size: ${escapeHTML(item.selectedSize)}</span>` : ""}
            </div>
            <b class="cart-item-price">${utils.formatCurrency(item.price)}</b>
            <div class="cart-qty-controls">
              <button class="qty-btn minus-qty" data-id="${item.id}">−</button>
              <span class="qty-num">${item.quantity}</span>
              <button class="qty-btn plus-qty" data-id="${item.id}">+</button>
            </div>
          </div>
          <button class="remove-cart-item-btn" data-id="${item.id}" aria-label="Remove">×</button>
        </div>
      `).join("") + `
        <div class="cart-drawer-actions">
          <button class="text-button cart-clear-btn">Clear bag</button>
          <button class="text-button cart-continue-btn">Continue shopping →</button>
        </div>`;
    }

    const subtotalEl = document.getElementById("cartSubtotalText");
    if (subtotalEl) subtotalEl.textContent = utils.formatCurrency(subtotal);

    container.querySelectorAll(".minus-qty").forEach(btn => {
      btn.onclick = () => this.updateQuantity(btn.dataset.id, -1);
    });

    container.querySelectorAll(".plus-qty").forEach(btn => {
      btn.onclick = () => this.updateQuantity(btn.dataset.id, 1);
    });

    container.querySelectorAll(".remove-cart-item-btn").forEach(btn => {
      btn.onclick = () => this.updateQuantity(btn.dataset.id, -999);
    });

    container.querySelectorAll(".cart-clear-btn").forEach(btn => {
      btn.onclick = () => {
        window.HRz.Storage.setCart([]);
        this.updateCartBadge();
        this.renderCartItems();
      };
    });

    container.querySelectorAll(".cart-continue-btn").forEach(btn => {
      btn.onclick = () => this.closeCart();
    });

    const checkoutBtn = document.getElementById("cartCheckoutBtn");
    if (checkoutBtn) {
      checkoutBtn.disabled = cart.length === 0;
      checkoutBtn.onclick = () => {
        // A durable guest choice is honoured here too: do not re-prompt
        // a returning guest on every checkout click.
        const go = () => {
          this.closeCart(false, true);
          window.location.hash = "checkout";
        };
        if (this._loginGatePassed()) {
          go();
        } else {
          this._promptForLogin(go, null);
        }
      };
    }
  }
}

window.HRz.Cart = CartDrawer;

