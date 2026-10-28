/* =============================================
   HRz PITSTOP – Product Detail Page & Trust Signals Module
   ============================================= */

window.HRz = window.HRz || {};

class ProductDetailView {
  static currentGallery = [];
  static currentGalleryIndex = 0;
  static viewerKeyHandler = null;

  static getGalleryImages(product) {
    const gallery = Array.isArray(product.gallery) ? product.gallery.filter(Boolean) : [];
    if (product.image && !gallery.includes(product.image)) {
      gallery.unshift(product.image);
    }
    return Array.from(new Set(gallery));
  }

  static ensureViewer() {
    let viewer = document.getElementById("productGalleryViewer");
    if (viewer) return viewer;

    viewer = document.createElement("div");
    viewer.id = "productGalleryViewer";
    viewer.className = "gallery-viewer";
    viewer.innerHTML = `
      <div class="gallery-viewer-backdrop" id="galleryViewerBackdrop"></div>
      <section class="gallery-viewer-panel" role="dialog" aria-modal="true" aria-label="Product image viewer">
        <button type="button" class="gallery-viewer-close" id="galleryViewerClose" aria-label="Close viewer">×</button>
        <button type="button" class="gallery-viewer-nav prev" id="galleryViewerPrev" aria-label="Previous image">←</button>
        <div class="gallery-viewer-stage">
          <img id="galleryViewerImage" src="" alt="Product image preview" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
        </div>
        <button type="button" class="gallery-viewer-nav next" id="galleryViewerNext" aria-label="Next image">→</button>
        <div class="gallery-viewer-meta">
          <strong id="galleryViewerTitle"></strong>
          <span id="galleryViewerCounter"></span>
        </div>
      </section>
    `;
    document.body.appendChild(viewer);

    viewer.querySelector("#galleryViewerBackdrop").onclick = () => this.closeViewer();
    viewer.querySelector("#galleryViewerClose").onclick = () => this.closeViewer();
    viewer.querySelector("#galleryViewerPrev").onclick = () => this.moveViewer(-1);
    viewer.querySelector("#galleryViewerNext").onclick = () => this.moveViewer(1);

    const stage = viewer.querySelector(".gallery-viewer-stage");
    if (stage) {
      let touchStartX = 0;
      let touchStartY = 0;

      stage.addEventListener("touchstart", (e) => {
        const touch = e.touches[0];
        if (!touch) return;
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
      }, { passive: true });

      stage.addEventListener("touchmove", (e) => {
        const touch = e.touches[0];
        if (!touch) return;
        const deltaX = touch.clientX - touchStartX;
        const deltaY = touch.clientY - touchStartY;
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
          e.preventDefault();
        }
      }, { passive: false });

      stage.addEventListener("touchend", (e) => {
        const touch = e.changedTouches[0];
        if (!touch) return;
        const deltaX = touch.clientX - touchStartX;
        const deltaY = touch.clientY - touchStartY;
        if (Math.abs(deltaX) > 45 && Math.abs(deltaX) > Math.abs(deltaY)) {
          this.moveViewer(deltaX < 0 ? 1 : -1);
        }
      });
    }

    if (!this.viewerKeyHandler) {
      this.viewerKeyHandler = (e) => {
        const activeViewer = document.getElementById("productGalleryViewer");
        if (!activeViewer || !activeViewer.classList.contains("open")) return;
        if (e.key === "Escape") this.closeViewer();
        if (e.key === "ArrowLeft") this.moveViewer(-1);
        if (e.key === "ArrowRight") this.moveViewer(1);
      };
      document.addEventListener("keydown", this.viewerKeyHandler);
    }

    return viewer;
  }

  static updateViewer() {
    const viewer = document.getElementById("productGalleryViewer");
    if (!viewer || !this.currentGallery.length) return;

    const image = viewer.querySelector("#galleryViewerImage");
    const title = viewer.querySelector("#galleryViewerTitle");
    const counter = viewer.querySelector("#galleryViewerCounter");

    if (image) image.src = this.currentGallery[this.currentGalleryIndex];
    if (title) title.textContent = "Swipe or use arrows to browse";
    if (counter) counter.textContent = `${this.currentGalleryIndex + 1} / ${this.currentGallery.length}`;
  }

  static openViewer(gallery, index = 0) {
    this.currentGallery = gallery;
    this.currentGalleryIndex = index;
    const viewer = this.ensureViewer();
    this.updateViewer();
    viewer.classList.add("open");
    document.body.classList.add("gallery-viewer-open");
    
    if (!window.history.state || !window.history.state.panelOpen) {
      window.history.pushState({ panelOpen: true }, "");
    }
  }

  static moveViewer(delta) {
    if (!this.currentGallery.length) return;
    this.currentGalleryIndex = (this.currentGalleryIndex + delta + this.currentGallery.length) % this.currentGallery.length;
    this.updateViewer();
  }

  static closeViewer(isPopState = false) {
    const viewer = document.getElementById("productGalleryViewer");
    const wasOpen = viewer && viewer.classList.contains("open");
    if (viewer) viewer.classList.remove("open");
    document.body.classList.remove("gallery-viewer-open");
    
    if (wasOpen && !isPopState && window.history.state && window.history.state.panelOpen) {
      window.history.back();
    }
  }

  static bindGalleryInteractions(container, gallery) {
    const mainFrame = container.querySelector(".main-image-frame");
    const mainImage = container.querySelector("#mainProductImage");
    const thumbs = Array.from(container.querySelectorAll(".thumb-btn"));

    const setActiveImage = (index) => {
      const safeIndex = (index + gallery.length) % gallery.length;
      const src = gallery[safeIndex];
      if (!src) return safeIndex;

      thumbs.forEach((thumb, thumbIndex) => thumb.classList.toggle("active", thumbIndex === safeIndex));
      if (mainImage) {
        mainImage.src = src;
        mainImage.dataset.galleryIndex = String(safeIndex);
      }
      const carousel = container.querySelector(".mobile-swipe-carousel");
      if (carousel && carousel.children[safeIndex]) {
        carousel.scrollTo({ left: carousel.children[safeIndex].offsetLeft, behavior: "smooth" });
      }
      return safeIndex;
    };

    const openAtCurrentImage = () => {
      const activeThumbIndex = thumbs.findIndex(btn => btn.classList.contains("active"));
      const currentIndex = activeThumbIndex >= 0 ? activeThumbIndex : Number(mainImage?.dataset.galleryIndex || 0);
      this.openViewer(gallery, currentIndex);
    };

    let suppressClick = false;

    if (mainFrame && mainImage) {
      mainImage.dataset.galleryIndex = "0";

      mainFrame.onmousemove = (e) => {
        const rect = mainFrame.getBoundingClientRect();
        const x = Math.min(100, Math.max(0, ((e.clientX - rect.left) / rect.width) * 100));
        const y = Math.min(100, Math.max(0, ((e.clientY - rect.top) / rect.height) * 100));
        mainFrame.style.setProperty("--zoom-x", `${x}%`);
        mainFrame.style.setProperty("--zoom-y", `${y}%`);
        mainFrame.classList.add("zooming");
      };

      mainFrame.onmouseleave = () => mainFrame.classList.remove("zooming");
      mainFrame.onclick = () => {
        if (suppressClick) return;
        openAtCurrentImage();
      };

      let touchStartX = 0;
      let touchStartY = 0;
      let touchMoved = false;

      mainFrame.addEventListener("touchstart", (e) => {
        const touch = e.touches[0];
        if (!touch) return;
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
        touchMoved = false;
      }, { passive: true });

      mainFrame.addEventListener("touchmove", (e) => {
        const touch = e.touches[0];
        if (!touch) return;
        const deltaX = touch.clientX - touchStartX;
        const deltaY = touch.clientY - touchStartY;

        if (Math.abs(deltaX) > 8 || Math.abs(deltaY) > 8) {
          touchMoved = true;
        }

        if (Math.abs(deltaX) > Math.abs(deltaY)) {
          e.preventDefault();
        }
      }, { passive: false });

      mainFrame.addEventListener("touchend", (e) => {
        const touch = e.changedTouches[0];
        if (!touch) return;
        const deltaX = touch.clientX - touchStartX;
        const deltaY = touch.clientY - touchStartY;

        if (Math.abs(deltaX) > 42 && Math.abs(deltaX) > Math.abs(deltaY)) {
          suppressClick = true;
          window.setTimeout(() => { suppressClick = false; }, 250);
          const currentIndex = Number(mainImage.dataset.galleryIndex || 0);
          setActiveImage(deltaX < 0 ? currentIndex + 1 : currentIndex - 1);
        } else if (!touchMoved) {
          openAtCurrentImage();
        }
      });
    }

    container.querySelectorAll(".carousel-image").forEach((img, index) => {
      img.onclick = () => {
        this.openViewer(gallery, index);
      };
    });

    thumbs.forEach((btn, index) => {
      btn.onclick = () => {
        setActiveImage(index);
        if (mainFrame) mainFrame.classList.remove("zooming");
        btn.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
      };
    });

    setActiveImage(Number(mainImage?.dataset.galleryIndex || 0));
  }

  // Fitment is "supported" for a real DB object ({isCompatible: true}) and
  // for a {supported: true} shape. It is NOT supported for null, for
  // {supported: false}, or for {isCompatible: false} — a truthy object
  // alone must never be read as a verified fit.
  static _isFitmentSupported(fitment) {
    if (!fitment) return false;
    if (fitment.supported === false || fitment.isCompatible === false) return false;
    return true;
  }

  // Related products, never empty when same-category products exist.
  // Fallback chain: bike-filtered same-category -> bike-filtered same-brand
  // -> bike-filtered rest -> all same-category -> all same-brand -> all.
  // (With a bike selected the bike-filtered pool is empty for real
  // products because no fitment data exists, so the all-products tiers
  // are what keep this section populated — honestly, without claiming
  // a fitment match.)
  static getRelatedProducts(product, activeBike) {
    const db = window.HRz.DB;
    if (!db) return [];
    let all = [];
    try {
      all = db.getProducts ? db.getProducts() : (db.products || []);
    } catch (e) {
      all = db.products || [];
    }
    all = Array.isArray(all) ? all.filter(p => p && p.id !== product.id) : [];
    let bikePool = [];
    try {
      bikePool = db.getProductsForBike ? db.getProductsForBike(activeBike) : all;
    } catch (e) {
      bikePool = [];
    }
    bikePool = Array.isArray(bikePool) ? bikePool.filter(p => p && p.id !== product.id) : [];
    const seen = new Set();
    const out = [];
    const pushFrom = (list) => {
      list.forEach(p => {
        if (p && !seen.has(p.id)) { seen.add(p.id); out.push(p); }
      });
    };
    pushFrom(bikePool.filter(p => p.category === product.category));
    pushFrom(bikePool.filter(p => p.brand === product.brand));
    pushFrom(bikePool);
    pushFrom(all.filter(p => p.category === product.category));
    pushFrom(all.filter(p => p.brand === product.brand));
    pushFrom(all);
    return out.slice(0, 4);
  }

  static render(container, productId, initialColor = null) {
    if (window.HRz.Storage && window.HRz.Storage.addRecentlyViewed) {
      window.HRz.Storage.addRecentlyViewed(productId);
    }

    const product = window.HRz.DB.getProductById(productId);
    const activeBike = window.HRz.Storage.getActiveBike();
    const escapeHTML = window.HRz.Utils.escapeHTML;

    if (!product) {
      container.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-icon">⚠️</div>
          <h3>Product Not Found or Unavailable</h3>
          <p>The motorcycle accessory or part you are looking for has been discontinued or moved.</p>
          <button class="accent-button" onclick="window.location.hash='catalog'">Return to Catalog</button>
        </div>
      `;
      return;
    }

    window.HRz.SEO.updateSEOForView("product", { product });

    let defaultVariantIdx = 0;
    if (product.variants && product.variants.length > 0) {
      if (initialColor) {
        const foundIdx = product.variants.findIndex(v => (v.color || v.name || "").toLowerCase().includes(initialColor.toLowerCase()));
        if (foundIdx !== -1) defaultVariantIdx = foundIdx;
      } else {
        const idIdx = product.variants.findIndex(v => v.id === product.id);
        if (idIdx !== -1) {
          defaultVariantIdx = idIdx;
        } else {
          const nameLower = (product.name || "").toLowerCase();
          const nameIdx = product.variants.findIndex(v => v.color && nameLower.includes(v.color.toLowerCase()));
          if (nameIdx !== -1) defaultVariantIdx = nameIdx;
        }
      }
    }

    const displayVariant = product.variants && product.variants.length > 0 ? product.variants[defaultVariantIdx] : null;
    const displayImage = displayVariant ? (displayVariant.image || product.image) : product.image;
    const displayPrice = displayVariant && displayVariant.price ? displayVariant.price : product.price;
    const detailDiscountPct = (product.originalPrice && Number(product.originalPrice) > Number(displayPrice))
      ? Math.round((1 - Number(displayPrice) / Number(product.originalPrice)) * 100) : 0;

    const fitment = window.HRz.DB.checkFitment(product.id, activeBike);
    const fitmentSupported = this._isFitmentSupported(fitment);
    const reviews = window.HRz.DB.getReviews().filter(r => r.productId === product.id && r.status === "published");
    const relatedProducts = this.getRelatedProducts(product, activeBike);
    const utils = window.HRz.Utils;
    const gallery = (displayVariant && displayVariant.gallery && displayVariant.gallery.length > 0)
      ? displayVariant.gallery
      : this.getGalleryImages(product);

    const STANDARD_SIZES = {
      'Riding Jackets & Apparel': ['S', 'M', 'L', 'XL', '2XL', '3XL'],
      'Helmets': ['S', 'M', 'L', 'XL', '2XL'],
      'Gloves': ['S', 'M', 'L', 'XL', '2XL'],
      'Riding Pants': ['30', '32', '34', '36', '38', '40'],
      'Boots & Footwear': ['UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11', 'UK 12']
    };
    const catStd = STANDARD_SIZES[product.category] || null;
    let availableSizes = [];
    if (Array.isArray(product.availableSizes)) {
      availableSizes = [...product.availableSizes];
    } else if (product.sizes) {
      availableSizes = product.sizes.split(',').map(s => s.trim()).filter(Boolean);
    }
    let allSizes = [];
    if (Array.isArray(product.allSizes) && product.allSizes.length) {
      allSizes = [...product.allSizes];
    } else if (availableSizes.length) {
      allSizes = catStd ? Array.from(new Set([...catStd, ...availableSizes])) : [...availableSizes];
    }
    const isWearableCategory = [
      'Helmets & Accessories', 'Helmets', 'Riding Jackets & Apparel', 'Riding Gears', 'Gloves', 'Riding Pants', 'Boots & Footwear'
    ].includes(product.category);
    const isNonWearableName = /(bluetooth|intercom|visor|spoiler|pinlock|mount|charger|lock|cable|cover|strap|clean|lube|fluid|care|kit|pad|holder|mechan|bag|carrier)/i.test(product.name || '');
    const isNonWearableSubcat = /(accessories|visor|clean|tech|mount|spoilers)/i.test(product.subcategory || '');

    if (!isWearableCategory || isNonWearableName || isNonWearableSubcat) {
      availableSizes = [];
      allSizes = [];
    }
    const defaultSelectedSize = availableSizes.length ? availableSizes[0] : (allSizes[0] || "");

    container.innerHTML = `
      <div class="breadcrumb-trail">
        <a href="#home">Home</a> / <a href="#catalog">Catalog</a> / <span class="current">${escapeHTML(product.name)}</span>
      </div>

      <div class="product-detail-layout">
        <!-- Media Gallery -->
        <div class="product-detail-gallery">
          <div class="gallery-badge-row">
            <span class="gallery-count-chip">${gallery.length} photo${gallery.length === 1 ? '' : 's'}</span>
          </div>
          <div class="main-image-frame desktop-only" role="button" tabindex="0" aria-label="Open product image viewer">
            <img id="mainProductImage" src="${escapeHTML(displayImage)}" alt="${escapeHTML(product.name)}" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
          </div>
          <div class="mobile-swipe-carousel mobile-only">
            ${gallery.map(img => `
              <img src="${escapeHTML(img)}" alt="${escapeHTML(product.name)}" class="carousel-image" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
            `).join("")}
          </div>
          <div class="thumbnail-strip">
            ${gallery.map((img, i) => `
              <button class="thumb-btn ${i === 0 ? "active" : ""}" data-src="${escapeHTML(img)}">
                <img src="${escapeHTML(img)}" alt="Thumbnail ${i+1}" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
              </button>
            `).join("")}
          </div>
        </div>

        <!-- Product Specs & Fitment -->
        <div class="product-detail-specs">
          <div class="sku-category-badge">${escapeHTML(product.category)} · SKU: <strong>${escapeHTML(product.sku)}</strong></div>
          <div class="detail-title-row">
            <h1 class="product-detail-title">${escapeHTML(product.name)}</h1>
            <button class="share-btn share-btn-icon" id="shareProductBtn" aria-label="Share product">↗</button>
          </div>

          ${product.variants && product.variants.length > 1 ? `
            <div class="product-variants-section">
              <h4>Select Color</h4>
              <div class="color-selector-grid">
                ${product.variants.map((v, idx) => `
                  <button class="color-btn ${idx === defaultVariantIdx ? 'active' : ''}" data-index="${idx}" title="${escapeHTML(v.color || v.name)}">
                    ${v.image ? `<img class="color-btn-img" src="${escapeHTML(v.image)}" alt="${escapeHTML(v.color || v.name)}" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />` : ''}
                    <span class="color-btn-text">${escapeHTML(v.color || v.name)}</span>
                  </button>
                `).join("")}
              </div>
            </div>
          ` : ""}

          <div class="product-detail-social">
            ${reviews.length
              ? `<span class="social-proof-text">(${reviews.length} Verified Rider Review${reviews.length === 1 ? "" : "s"})</span>`
              : `<span class="social-proof-text">No verified rider reviews yet</span>`}
          </div>

          <div class="detail-price-box">
            <div class="price-row">
              <span class="detail-price">${utils.formatCurrency(displayPrice)}</span>
              ${(product.originalPrice && Number(product.originalPrice) > Number(displayPrice)) ? `<span class="detail-original-price">${utils.formatCurrency(product.originalPrice)}</span>` : ""}
              ${detailDiscountPct > 0 ? `<span class="discount-badge">${detailDiscountPct}% OFF</span>` : ""}
              <span class="tax-inclusive-tag">Inclusive of all taxes & free shipping</span>
            </div>
          </div>

          <div class="fitment-guarantee-banner ${fitmentSupported ? "verified-fit" : "universal-fit"}">
            <div class="banner-icon">${fitmentSupported ? "🛡️" : "🔧"}</div>
            <div class="banner-content">
              <strong>${fitmentSupported ? `100% Guaranteed OEM Fit for ${activeBike ? escapeHTML(activeBike.brand) + " " + escapeHTML(activeBike.model) : "Your Motorcycle"}` : (activeBike ? `Fitment not verified for ${escapeHTML(activeBike.brand)} ${escapeHTML(activeBike.model)}` : "Universal Motorcycle Compatibility")}</strong>
              <p>${fitmentSupported ? escapeHTML(fitment.notes || "Verified fitment for your motorcycle.") : (activeBike ? "Fitment data not available for this bike yet — please confirm fitment with us before ordering." : "Compatible with standard motorcycle mounts & clamps.")}</p>
            </div>
          </div>

          ${(allSizes && allSizes.length > 0) ? `
            <div class="product-size-section">
              <div class="size-header-row">
                <span class="size-heading">SELECT SIZE: <strong id="selectedSizeDisplay">${escapeHTML(defaultSelectedSize || "STANDARD")}</strong></span>
                <span class="size-guide-hint">Standard Rider Fit</span>
              </div>
              <div class="size-pills-grid" id="sizePillsGrid">
                ${allSizes.map(s => {
                  const isAvail = availableSizes.includes(s);
                  const isAct = isAvail && (s === defaultSelectedSize);
                  if (isAvail) {
                    return `<button type="button" class="size-pill-btn ${isAct ? 'active' : ''}" data-size="${escapeHTML(s)}" aria-label="Select size ${escapeHTML(s)}">${escapeHTML(s)}</button>`;
                  } else {
                    return `<button type="button" class="size-pill-btn disabled" data-size="${escapeHTML(s)}" disabled title="Size ${escapeHTML(s)} currently unavailable" aria-disabled="true"><span class="size-strike-text">${escapeHTML(s)}</span></button>`;
                  }
                }).join("")}
              </div>
            </div>
          ` : ""}

          <div class="purchase-actions-row">
            <button class="add-to-bag-hero-btn" id="addToBagHeroBtn">
              Add to Bag
            </button>
            <div class="detail-bag-stepper" id="detailBagStepper" style="display:none;">
              <button class="qty-btn detail-bag-minus" aria-label="Decrease quantity">−</button>
              <span class="qty-num" id="detailBagQty">1</span>
              <button class="qty-btn detail-bag-plus" aria-label="Increase quantity">+</button>
            </div>
            <button class="buy-now-btn" id="buyNowBtn">
              Buy Now
            </button>
          </div>
          <div class="delivery-estimate">
            <strong>🚚 Dispatched within 24 hours.</strong> FREE Express Shipping across India on orders above ₹2,999 (flat ₹199 below that). Exact delivery date is confirmed with you on WhatsApp before you pay.
          </div>
          <div style="margin-top: 12px; margin-bottom: 24px;">
            <button class="text-button report-fitment-issue-btn" id="reportFitmentIssueBtn" style="color: var(--mute); text-decoration: underline; font-size: 12px; background: none; border: none; padding: 0; cursor: pointer;">
              Didn't Fit My Bike?
            </button>
          </div>

          <!-- Trust Badges Strip -->
          <div class="detail-trust-grid">
            <div class="trust-pill"><span class="icon">✅</span> 7-Day Free Fitment Return Guarantee</div>
            <div class="trust-pill"><span class="icon">📜</span> ${escapeHTML(product.authenticity || "100% OEM Certified")}</div>
            <div class="trust-pill"><span class="icon">🔒</span> ${escapeHTML(product.warranty || "12 Months Warranty")}</div>
          </div>

          ${product.description ? `
            <div class="product-description-box" style="margin-top:24px; color:var(--mute); font-size:14px; line-height:1.6;">
              <p>${escapeHTML(product.description)}</p>
            </div>
          ` : ""}

          <div class="product-highlights-box">
            <h3>Key Features & Rider Specifications</h3>
            <ul>
              ${(product.highlights || []).map(h => `<li><span class="bullet">▶</span> ${escapeHTML(h)}</li>`).join("")}
            </ul>
          </div>
        </div>
      </div>

      <!-- Real Installation Photos & Bike-Specific Reviews Section -->
      <section class="rider-proof-section">
        <div class="section-title-row">
          <div>
            <p class="eyebrow">Installation Gallery</p>
            <h2>Installation Photos</h2>
          </div>
        </div>

        <div class="installation-photos-carousel">
          <h4>Customer Installation Gallery</h4>
          <div class="install-grid">
            <div class="install-card">
              <img src="${escapeHTML(displayImage)}" alt="Installation" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
              <div class="install-caption">
                <strong>Illustrative installation photo</strong>
                <small>Example fitment photo</small>
              </div>
            </div>
            <div class="install-card">
              <img src="images/crash_guard_product.webp" alt="Installation" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
              <div class="install-caption">
                <strong>Illustrative installation photo</strong>
                <small>Example fitment photo</small>
              </div>
            </div>
          </div>
        </div>

        <div class="reviews-list">
          ${reviews.length === 0 ? `
            <p class="no-reviews-text">No reviews published yet for this bike model. Be the first rider to submit an installation review!</p>
          ` : `
            ${reviews.map(r => `
              <div class="review-card">
                <div class="review-header">
                  <span class="reviewer-name">${escapeHTML(r.reviewerName)}</span>
                  <span class="review-bike-tag">Verified ${escapeHTML(r.bikeName)}</span>
                  <span class="review-date">${escapeHTML(r.date)}</span>
                </div>
                <div class="review-rating">${utils.renderStarRating(r.rating)}</div>
                <h4 class="review-title">${escapeHTML(r.title)}</h4>
                <p class="review-comment">${escapeHTML(r.comment)}</p>
              </div>
            `).join("")}
          `}
        </div>
      </section>

      ${relatedProducts.length ? `
        <section class="rider-proof-section related-products-section">
          <div class="section-title-row">
            <div>
              <p class="eyebrow red">Recommended next</p>
              <h2>Related Products</h2>
            </div>
          </div>
          <div class="product-grid inner-section related-products-grid">
            ${relatedProducts.map(p => window.HRz.Catalog.renderProductCard(p, activeBike, window.HRz.Storage.getWishlist())).join("")}
          </div>
        </section>
      ` : ""}

      <div class="sticky-buy-bar">
        <button class="capsule-add-btn" id="stickyAddBtn">Add to Bag</button>
        <div class="card-qty-stepper" id="stickyStepper" style="display:none;">
          <button class="qty-btn sticky-qty-minus" aria-label="Decrease quantity">−</button>
          <span class="qty-num" id="stickyQtyNum">1</span>
          <button class="qty-btn sticky-qty-plus" aria-label="Increase quantity">+</button>
        </div>
        <button class="capsule-buy-btn" id="stickyBuyBtn">Buy Now</button>
      </div>
    `;

    this.bindGalleryInteractions(container, gallery);

    const mainFrame = container.querySelector(".main-image-frame");
    if (mainFrame) {
      mainFrame.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          const activeThumbIndex = Array.from(container.querySelectorAll(".thumb-btn")).findIndex(btn => btn.classList.contains("active"));
          this.openViewer(gallery, activeThumbIndex >= 0 ? activeThumbIndex : 0);
        }
      };
    }

    this.bindVariantEvents(product, container);

    let currentSelectedSize = defaultSelectedSize;

    container.querySelectorAll(".size-pill-btn:not(.disabled)").forEach(btn => {
      btn.onclick = () => {
        const sz = btn.dataset.size;
        if (!sz) return;
        currentSelectedSize = sz;
        container.querySelectorAll(".size-pill-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const displayEl = container.querySelector("#selectedSizeDisplay");
        if (displayEl) displayEl.textContent = sz;

        const sizeVar = (Array.isArray(product.sizeVariants)
          ? product.sizeVariants.find(v => (v.size || '').toUpperCase() === sz.toUpperCase())
          : (product.sizeVariants ? (product.sizeVariants[sz] || product.sizeVariants[sz.toUpperCase()]) : null));
        if (sizeVar && sizeVar.price) {
          const priceEl = container.querySelector(".detail-price");
          if (priceEl) priceEl.textContent = utils.formatCurrency(sizeVar.price);
        }

        syncDetailBagState();
      };
    });

    // One buy control per screen: the stepper IS the quantity control, so
    // there is no separate quantity selector anymore. Desktop uses the
    // in-flow purchase row; mobile uses the pinned bottom capsule. Both
    // share this state: first add puts 1 in the bag, the stepper adjusts.
    const buildBuyCopy = () => {
      let pCopy = { ...product };
      const activeColorBtn = container.querySelector(".color-btn.active");
      if (activeColorBtn && product.variants) {
        const v = product.variants[activeColorBtn.dataset.index];
        if (v) {
          pCopy.image = v.image || pCopy.image;
          pCopy.price = v.price || pCopy.price;
          pCopy.color = v.color || v.name || pCopy.color;
          // The base id IS the default variant: a card add (base id) and a
          // product-page add for the default variant are the same bag
          // entry, so quantities never disagree between card and page.
          // Only non-default variants get a suffixed id.
          const activeIdx = Number(activeColorBtn.dataset.index);
          const isDefault = (typeof defaultVariantIdx === "number" && activeIdx === defaultVariantIdx);
          if (!isDefault) {
            pCopy.id = pCopy.id + "-" + (v.color || v.name || "").toLowerCase().replace(/[^a-z0-9]/g, '-');
          }
        }
      }

      if (currentSelectedSize) {
        pCopy.selectedSize = currentSelectedSize;
        const sizeVar = (Array.isArray(product.sizeVariants)
          ? product.sizeVariants.find(v => (v.size || '').toUpperCase() === currentSelectedSize.toUpperCase())
          : (product.sizeVariants ? (product.sizeVariants[currentSelectedSize] || product.sizeVariants[currentSelectedSize.toUpperCase()]) : null));
        if (sizeVar) {
          if (sizeVar.id) pCopy.id = sizeVar.id;
          if (sizeVar.sku) pCopy.sku = sizeVar.sku;
          if (sizeVar.price) pCopy.price = sizeVar.price;
          if (sizeVar.image) pCopy.image = sizeVar.image;
        } else {
          pCopy.id = `${pCopy.id}-size-${currentSelectedSize.toLowerCase().replace(/[^a-z0-9]/g, '')}`;
        }
      }

      return pCopy;
    };

    // Bag-state sync: once the current variant is in the bag, Add to Bag
    // becomes a stepper (desktop row + mobile capsule) instead of offering
    // a fresh add. Variant switches re-sync, since each variant has its
    // own bag entry.
    const addBtn = container.querySelector("#addToBagHeroBtn");
    const stickyAddBtn = container.querySelector("#stickyAddBtn");
    const detailBagStepper = container.querySelector("#detailBagStepper");
    const detailBagQty = container.querySelector("#detailBagQty");
    const stickyStepper = container.querySelector("#stickyStepper");
    const stickyQtyNum = container.querySelector("#stickyQtyNum");
    const getBagQtyForBuyCopy = () => {
      try {
        const copy = buildBuyCopy();
        const cart = (window.HRz.Storage && typeof window.HRz.Storage.getCart === "function") ? window.HRz.Storage.getCart() : [];
        const item = cart.find(i => i.id === copy.id || (i.name === copy.name && i.selectedSize === copy.selectedSize));
        return { qty: item ? (Number(item.quantity) || 0) : 0, id: item ? item.id : copy.id };
      } catch (e) { return { qty: 0, id: null }; }
    };
    const syncDetailBagState = () => {
      const { qty } = getBagQtyForBuyCopy();
      const inBag = qty > 0;
      if (addBtn) addBtn.style.display = inBag ? "none" : "";
      if (detailBagStepper) detailBagStepper.style.display = inBag ? "inline-flex" : "none";
      if (inBag && detailBagQty) detailBagQty.textContent = String(qty);
      if (stickyAddBtn) stickyAddBtn.style.display = inBag ? "none" : "";
      if (stickyStepper) stickyStepper.style.display = inBag ? "inline-flex" : "none";
      if (inBag && stickyQtyNum) stickyQtyNum.textContent = String(qty);
    };
    const stepDetailBag = (delta) => {
      const { id } = getBagQtyForBuyCopy();
      if (!id) return;
      if (window.HRz.Cart && typeof window.HRz.Cart.updateQuantity === "function") {
        window.HRz.Cart.updateQuantity(id, delta);
      }
      syncDetailBagState();
    };
    const addToBagOnce = () => {
      window.dispatchEvent(new CustomEvent("hrz:add-to-cart", { detail: { product: buildBuyCopy(), quantity: 1 } }));
      syncDetailBagState();
    };
    if (addBtn) addBtn.onclick = addToBagOnce;
    if (stickyAddBtn) stickyAddBtn.onclick = addToBagOnce;
    container.querySelectorAll(".detail-bag-minus, .sticky-qty-minus").forEach(btn => {
      btn.onclick = () => stepDetailBag(-1);
    });
    container.querySelectorAll(".detail-bag-plus, .sticky-qty-plus").forEach(btn => {
      btn.onclick = () => stepDetailBag(1);
    });
    // Variant switches change the bag entry: re-sync after the variant
    // handler (registered first) has updated the active button.
    container.querySelectorAll(".color-btn").forEach(btn => {
      btn.addEventListener("click", () => syncDetailBagState());
    });
    syncDetailBagState();

    const shareBtn = container.querySelector("#shareProductBtn");
    if (shareBtn) {
      shareBtn.onclick = async () => {
        const url = `${window.location.origin}${window.location.pathname}#product?id=${encodeURIComponent(product.id)}`;
        const shareData = { title: product.name, text: `${product.name} — ${utils.formatCurrency(displayPrice)} at HRZ Pitstop`, url };
        try {
          if (navigator.share) { await navigator.share(shareData); return; }
          throw new Error("no-share");
        } catch (e) {
          try {
            await navigator.clipboard.writeText(url);
            window.HRz.Utils.showToast("Product link copied", "success");
          } catch (e2) {
            window.HRz.Utils.showToast("Share this link: " + url, "info");
          }
        }
      };
    }

    // Buy Now buys the stepper quantity when the item is in the bag,
    // otherwise 1 — the stepper is the only quantity control now.
    const buyNowWithQty = () => {
      const pCopy = buildBuyCopy();
      const { qty } = getBagQtyForBuyCopy();
      const buyQty = qty > 0 ? qty : 1;
      // Single shared BUY NOW path in cart.js (adds once, closes any
      // drawer, goes to checkout). Catalog quick-view BUY NOW should
      // call the same Cart.buyNow / dispatch "hrz:buy-now".
      if (window.HRz.Cart && typeof window.HRz.Cart.buyNow === "function") {
        window.HRz.Cart.buyNow(pCopy, { quantity: buyQty });
      } else if (window.HRz.Cart) {
        window.HRz.Cart.addItem(pCopy, { suppressDrawer: true, quantity: buyQty });
        window.HRz.Cart.closeCart(false, true);
        window.location.hash = "checkout";
      }
    };

    const buyNowBtn = container.querySelector("#buyNowBtn");
    if (buyNowBtn) buyNowBtn.onclick = buyNowWithQty;

    const stickyBuyBtn = container.querySelector("#stickyBuyBtn");
    if (stickyBuyBtn) stickyBuyBtn.onclick = buyNowWithQty;

    const reportBtn = container.querySelector("#reportFitmentIssueBtn");
    if (reportBtn) {
      reportBtn.onclick = () => this.openFitmentReportModal(product, activeBike);
    }

    // Related-product cards use the shared card renderer, so they need the
    // shared card bindings (+ Bag / stepper / wishlist) — previously dead.
    if (window.HRz.Catalog && typeof window.HRz.Catalog.bindCardEvents === "function") {
      window.HRz.Catalog.bindCardEvents(container);
    }
  }

  static openFitmentReportModal(product, activeBike) {
    let modal = document.getElementById("fitmentReportModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "fitmentReportModal";
      modal.className = "modal-overlay";
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <p class="eyebrow">Fitment Guarantee</p>
            <h3>Report Fitment Discrepancy</h3>
          </div>
          <button type="button" class="close-btn" id="closeReportModal">✕</button>
        </div>
        <div class="modal-body">
          <p>We take fitment accuracy very seriously. If <strong>${window.HRz.Utils.escapeHTML(product.name)}</strong> did not fit your <strong>${activeBike ? window.HRz.Utils.escapeHTML(activeBike.brand) + " " + window.HRz.Utils.escapeHTML(activeBike.model) : "motorcycle"}</strong>, let us know for an instant return label.</p>

          <form id="fitmentReportForm">
            <div class="form-group">
              <label>Your Bike Variant</label>
              <input type="text" value="${activeBike ? window.HRz.Utils.escapeHTML(activeBike.brand) + ' ' + window.HRz.Utils.escapeHTML(activeBike.model) + ' ' + window.HRz.Utils.escapeHTML(activeBike.variant) : 'Motorcycle'}" readonly />
            </div>
            <div class="form-group">
              <label for="fitmentIssueType">Issue Encountered</label>
              <select id="fitmentIssueType" required>
                <option value="bolt-alignment">Bolt Holes Do Not Align</option>
                <option value="clearance">Clearance Issue with Tank/Fairing</option>
                <option value="missing-bracket">Missing Adapter Bracket</option>
                <option value="wrong-sku">Received Wrong SKU Variant</option>
              </select>
            </div>
            <div class="form-group">
              <label for="fitmentDetails">Detailed Explanation</label>
              <textarea id="fitmentDetails" rows="3" placeholder="Describe where it failed to mount..." required></textarea>
            </div>
            <button type="submit" class="accent-button full-width-btn">Submit Fitment Claim</button>
          </form>
        </div>
      </div>
    `;

    modal.classList.add("show");
    window.HRz.Utils.setupModalAccessibility(modal, () => this.closeFitmentModal());
    
    if (!window.history.state || !window.history.state.panelOpen) {
      window.history.pushState({ panelOpen: true }, "");
    }

    document.getElementById("closeReportModal").onclick = () => this.closeFitmentModal();

    document.getElementById("fitmentReportForm").onsubmit = (e) => {
      e.preventDefault();
      this.closeFitmentModal();
      window.HRz.Utils.showToast("Fitment report submitted. Our technical team will reach out within 2 hours with a return waybill.", "success");
    };
  }

  static closeFitmentModal(isPopState = false) {
    const modal = document.getElementById("fitmentReportModal");
    const wasOpen = modal && modal.classList.contains("show");
    if (modal) modal.classList.remove("show");
    
    if (wasOpen && !isPopState && window.history.state && window.history.state.panelOpen) {
      window.history.back();
    }
  }

  static bindVariantEvents(product, container) {
    if (!product.variants || product.variants.length <= 1) return;
    
    const root = container || document;
    const colorBtns = root.querySelectorAll(".color-btn");
    const mainImg = root.querySelector("#mainProductImage");
    const thumbStrip = root.querySelector(".thumbnail-strip");
    const carouselStrip = root.querySelector(".mobile-swipe-carousel");
    const priceDisplay = root.querySelector(".detail-price");
    const origPriceDisplay = root.querySelector(".detail-original-price");
    const skuBadge = root.querySelector(".sku-category-badge strong");
    const countChip = root.querySelector(".gallery-count-chip");

    colorBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        colorBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        
        const v = product.variants[btn.dataset.index];
        if (!v) return;
        
        if (priceDisplay && v.price) priceDisplay.textContent = window.HRz.Utils.formatCurrency(v.price);
        if (origPriceDisplay && v.price) origPriceDisplay.textContent = window.HRz.Utils.formatCurrency(Math.round(v.price * 1.15));
        if (skuBadge && v.sku) skuBadge.textContent = v.sku;
        if (mainImg && v.image) mainImg.src = v.image;
        
        const variantGallery = (v.gallery && v.gallery.length > 0) ? v.gallery : [v.image || product.image].filter(Boolean);
        
        if (countChip) {
          countChip.textContent = `${variantGallery.length} photo${variantGallery.length === 1 ? '' : 's'}`;
        }
        
        if (thumbStrip) {
           thumbStrip.innerHTML = variantGallery.map((img, i) => `
              <button class="thumb-btn ${i === 0 ? "active" : ""}" data-src="${window.HRz.Utils.escapeHTML(img)}">
                <img src="${window.HRz.Utils.escapeHTML(img)}" alt="Thumbnail ${i+1}" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
              </button>
           `).join("");
        }
           
        if (carouselStrip) {
           carouselStrip.innerHTML = variantGallery.map(img => `
             <img src="${window.HRz.Utils.escapeHTML(img)}" alt="${window.HRz.Utils.escapeHTML(product.name)}" class="carousel-image" loading="lazy" onerror="this.onerror=null;this.src=window.HRzPlaceholderImage" />
           `).join("");
        }
        
        if (container) {
          this.bindGalleryInteractions(container, variantGallery);
        }
      });
    });
  }
}

window.HRz.Product = ProductDetailView;
