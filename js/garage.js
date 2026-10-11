/* =============================================
   HRz PITSTOP – Garage & Bike Selector Module
   ============================================= */

window.HRz = window.HRz || {};

class GarageManager {
  static init(onBikeChangedCallback) {
    this.onBikeChanged = onBikeChangedCallback;
    this.updateActiveBikeUI();
    this.bindEvents();
  }

  static updateActiveBikeUI() {
    const activeBike = window.HRz.Storage.getActiveBike();
    const chipInfo = document.getElementById("activeBikeChip");
    const escapeHTML = window.HRz.Utils.escapeHTML;
    
    if (chipInfo) {
      if (activeBike) {
        chipInfo.innerHTML = `
          <strong>${escapeHTML(activeBike.brand)} ${escapeHTML(activeBike.model)}</strong>
          <small>${escapeHTML(activeBike.variant || "")} (${escapeHTML(activeBike.year || "")})</small>
        `;
      } else {
        chipInfo.innerHTML = `
          <strong>Select Your Bike</strong>
          <small>Filter by model</small>
        `;
      }
    }
  }

  static bindEvents() {
    const openBtn = document.getElementById("openBikeModal");
    if (openBtn) {
      openBtn.onclick = () => this.openBikeModal();
    }
  }

  static openBikeModal() {
    let modal = document.getElementById("bikeSelectorModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "bikeSelectorModal";
      modal.className = "modal-overlay";
      document.body.appendChild(modal);
    }

    const bikes = window.HRz.DB.getBikes();
    
    const brandsMap = {};
    bikes.forEach(b => {
      if (!brandsMap[b.brand]) brandsMap[b.brand] = {};
      if (!brandsMap[b.brand][b.model]) brandsMap[b.brand][b.model] = [];
      brandsMap[b.brand][b.model].push(b);
    });

    const brands = Object.keys(brandsMap);
    const escapeHTML = window.HRz.Utils.escapeHTML;

    modal.innerHTML = `
      <div class="modal-card bike-selector-card">
        <div class="modal-header">
          <div>
            <p class="eyebrow">Motorcycle Compatibility</p>
            <h3>Select Your Motorcycle</h3>
          </div>
          <button type="button" class="close-btn" id="closeBikeModalBtn" aria-label="Close modal">✕</button>
        </div>
        <div class="modal-body">
          <p class="modal-subtitle">Choose your exact make and variant to see guaranteed fitment parts only.</p>
          
          <form id="bikeSelectForm" class="bike-select-form">
            <div class="form-group">
              <label for="selectBrand">1. Select Brand / Make</label>
              <select id="selectBrand" required>
                <option value="">-- Choose Brand --</option>
                ${brands.map(b => `<option value="${escapeHTML(b)}">${escapeHTML(b)}</option>`).join("")}
              </select>
            </div>
            <div class="form-group">
              <label for="selectModel">2. Select Model</label>
              <select id="selectModel" disabled required>
                <option value="">-- Choose Model --</option>
              </select>
            </div>
            <div class="form-group">
              <label for="selectVariant">3. Select Variant & Year</label>
              <select id="selectVariant" disabled required>
                <option value="">-- Choose Variant --</option>
              </select>
            </div>
            
            <button type="submit" class="accent-button full-width-btn" id="confirmBikeBtn" disabled>
              Set Active Bike & Filter Catalog
            </button>
          </form>

          <div class="quick-presets-section">
            <p class="section-label">Or Pick Popular Presets:</p>
            <div class="presets-grid">
              <button type="button" class="preset-chip" data-brand="Royal Enfield" data-model="Himalayan 450" data-variant="450 Adventure" data-year="2024">
                <strong>Royal Enfield</strong> Himalayan 450
              </button>
              <button type="button" class="preset-chip" data-brand="KTM" data-model="Duke 390 Gen-3" data-variant="Gen-3 Standard" data-year="2024">
                <strong>KTM</strong> Duke 390
              </button>
              <button type="button" class="preset-chip" data-brand="Triumph" data-model="Speed 400" data-variant="Roadster" data-year="2024">
                <strong>Triumph</strong> Speed 400
              </button>
              <button type="button" class="preset-chip" data-brand="Yamaha" data-model="MT-15 V2" data-variant="V2 Deluxe" data-year="2024">
                <strong>Yamaha</strong> MT-15
              </button>
              <button type="button" class="preset-chip" data-brand="BMW" data-model="G 310 GS" data-variant="Rallye Style" data-year="2024">
                <strong>BMW</strong> G 310 GS
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    modal.classList.add("show");
    window.HRz.Utils.setupModalAccessibility(modal, () => this.closeBikeModal());

    const closeBtn = document.getElementById("closeBikeModalBtn");
    if (closeBtn) closeBtn.onclick = () => this.closeBikeModal();

    const brandSel = document.getElementById("selectBrand");
    const modelSel = document.getElementById("selectModel");
    const variantSel = document.getElementById("selectVariant");
    const submitBtn = document.getElementById("confirmBikeBtn");

    brandSel.onchange = () => {
      const selectedBrand = brandSel.value;
      modelSel.innerHTML = `<option value="">-- Choose Model --</option>`;
      variantSel.innerHTML = `<option value="">-- Choose Variant --</option>`;
      variantSel.disabled = true;
      submitBtn.disabled = true;

      if (selectedBrand && brandsMap[selectedBrand]) {
        const models = Object.keys(brandsMap[selectedBrand]);
        models.forEach(m => {
          modelSel.innerHTML += `<option value="${escapeHTML(m)}">${escapeHTML(m)}</option>`;
        });
        modelSel.disabled = false;
        modelSel.focus();
      } else {
        modelSel.disabled = true;
      }
    };

    modelSel.onchange = () => {
      const selectedBrand = brandSel.value;
      const selectedModel = modelSel.value;
      variantSel.innerHTML = `<option value="">-- Choose Variant --</option>`;
      submitBtn.disabled = true;

      if (selectedBrand && selectedModel && brandsMap[selectedBrand][selectedModel]) {
        const variantsList = brandsMap[selectedBrand][selectedModel];
        variantsList.forEach(v => {
          variantSel.innerHTML += `<option value="${escapeHTML(v.id)}">${escapeHTML(v.variant)} (${escapeHTML(v.year)})</option>`;
        });
        variantSel.disabled = false;
        
        // Auto-select and auto-submit if there is only 1 variant
        if (variantsList.length === 1) {
          variantSel.value = variantsList[0].id;
          submitBtn.disabled = false;
          this.selectBike(variantsList[0]);
        } else {
          variantSel.focus();
        }
      } else {
        variantSel.disabled = true;
      }
    };

    variantSel.onchange = () => {
      submitBtn.disabled = !variantSel.value;
      if (variantSel.value) {
        const bikeId = variantSel.value;
        const bikeObj = bikes.find(b => b.id === bikeId);
        if (bikeObj) {
          this.selectBike(bikeObj);
        }
      }
    };

    document.getElementById("bikeSelectForm").onsubmit = (e) => {
      e.preventDefault();
      const bikeId = variantSel.value;
      const bikeObj = bikes.find(b => b.id === bikeId);
      if (bikeObj) {
        this.selectBike(bikeObj);
      }
    };

    modal.querySelectorAll(".preset-chip").forEach(chip => {
      chip.onclick = (e) => {
        e.preventDefault();
        const { brand, model, variant, year } = chip.dataset;
        const found = bikes.find(b => b.brand === brand && b.model === model && b.variant === variant);
        const targetBike = found || { nickname: `${brand} ${model}`, brand, model, variant, year: parseInt(year), bikeId: `bike-${brand.toLowerCase()}` };
        this.selectBike(targetBike);
      };
    });
  }

  static selectBike(bikeObj) {
    const active = window.HRz.Storage.setActiveBike({
      nickname: `${bikeObj.brand} ${bikeObj.model}`,
      brand: bikeObj.brand,
      model: bikeObj.model,
      year: bikeObj.year || 2024,
      variant: bikeObj.variant,
      bikeId: bikeObj.id || `bike-${Date.now()}`,
      category: bikeObj.category || ""
    });

    this.updateActiveBikeUI();
    this.closeBikeModal();
    window.HRz.Utils.showToast(`Showing parts for ${active.brand} ${active.model} in Garage ↗`, "success");

    // Navigate to garage so the bike selector and recommendations stay together
    setTimeout(() => { window.location.hash = "garage"; }, 250);

    if (this.onBikeChanged) {
      this.onBikeChanged(active);
    }
  }

  static closeBikeModal() {
    const modal = document.getElementById("bikeSelectorModal");
    if (modal) {
      modal.classList.remove("show");
    }
  }

  static renderGarageView(container) {
    const db = window.HRz.DB;
    const catalog = window.HRz.Catalog;
    const garage = window.HRz.Storage.getGarage();
    const activeBike = window.HRz.Storage.getActiveBike();
    const recommendedProducts = db.getRecommendedProducts(activeBike, null, 10);
    const escapeHTML = window.HRz.Utils.escapeHTML;

    container.innerHTML = `
      <div class="view-header">
        <div>
          <p class="eyebrow">My Fleet & Compatibility</p>
          <h2>My Garage</h2>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
          <button class="accent-button" id="addNewBikeGarageBtn">Choose Your Bike</button>
          <a class="secondary-button" href="#catalog">Browse All Products</a>
        </div>
      </div>

      <section class="garage-selector-block" style="margin: 24px 0 32px; padding: 24px; border: 1px solid #222; border-radius: 18px; background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));">
        <div class="section-head" style="margin-bottom: 16px;">
          <div>
            <p class="eyebrow red">Choose your ride</p>
            <h2>${activeBike ? `${escapeHTML(activeBike.brand)} ${escapeHTML(activeBike.model)}` : "Pick a Bike"}</h2>
          </div>
          <p style="max-width: 620px; color: var(--mute);">Select a bike below to view guaranteed fitment parts for your motorcycle.</p>
        </div>

        <div class="garage-chip-row" style="display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-bottom:16px;">
          <div id="activeBikeChip" class="bike-chip" style="min-width: 240px;">
            ${activeBike ? `
              <strong>${escapeHTML(activeBike.brand)} ${escapeHTML(activeBike.model)}</strong>
              <small>${escapeHTML(activeBike.variant || "")} (${escapeHTML(activeBike.year || "")})</small>
            ` : `
              <strong>Select Your Bike</strong>
              <small>to filter the demo catalog</small>
            `}
          </div>
          
        </div>

        <div class="product-grid inner-section" id="garageRecommendationGrid">
          ${recommendedProducts.length ? recommendedProducts.map(p => catalog.renderProductCard(p, activeBike, window.HRz.Storage.getWishlist())).join("") : `<div class="empty-state-card"><p>No matches yet. Pick a bike to see related demo products.</p></div>`}
        </div>
      </section>

      <div class="section-head" style="margin-top: 12px;">
        <div>
          <p class="eyebrow red">Saved vehicles</p>
          <h2>Garage List</h2>
        </div>
      </div>

      ${garage.length === 0 ? `
        <div class="empty-state-card">
          <div class="empty-icon">🏍️</div>
          <h3>No bikes saved yet</h3>
          <p>Add your motorcycle above to get started.</p>
        </div>
      ` : `
        <div class="garage-grid">
          ${garage.map(bike => {
            const isActive = activeBike && activeBike.brand === bike.brand && activeBike.model === bike.model && activeBike.variant === bike.variant;
            return `
              <div class="garage-card ${isActive ? "active-garage-card" : ""}">
                <div class="garage-card-header">
                  <span class="bike-badge">${escapeHTML(bike.brand)}</span>
                  ${isActive ? `<span class="active-tag">Active Vehicle</span>` : ""}
                </div>
                <h3>${escapeHTML(bike.brand)} ${escapeHTML(bike.model)}</h3>
                <p class="variant-text">${escapeHTML(bike.variant)} · Year ${escapeHTML(bike.year)}</p>
                <div class="garage-card-actions">
                  ${!isActive ? `<button class="secondary-button activate-bike-btn" data-id="${escapeHTML(bike.bikeId)}">Set Active</button>` : `<span class="active-status-text">✓ Currently Filtering Catalog</span>`}
                  <button class="icon-button remove-bike-btn" data-id="${escapeHTML(bike.bikeId)}" title="Remove from garage">🗑️</button>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      `}
    `;

    const addBtn = container.querySelector("#addNewBikeGarageBtn");
    if (addBtn) addBtn.onclick = () => this.openBikeModal();

    const topOpenBtn = container.querySelector("#openBikeModalTopBtn");
    if (topOpenBtn) topOpenBtn.onclick = () => this.openBikeModal();

    container.querySelectorAll(".activate-bike-btn").forEach(btn => {
      btn.onclick = () => {
        const id = btn.dataset.id;
        const target = garage.find(g => g.bikeId === id);
        if (target) this.selectBike(target); // selectBike now navigates to catalog
      };
    });

    container.querySelectorAll(".remove-bike-btn").forEach(btn => {
      btn.onclick = () => {
        const id = btn.dataset.id;
        window.HRz.Storage.removeBikeFromGarage(id);
        this.renderGarageView(container);
        this.updateActiveBikeUI();
        window.HRz.Utils.showToast("Bike removed from garage", "info");
      };
    });

    // Bind events for the product cards in the garage view
    catalog.bindCardEvents(container);
  }
}

window.HRz.Garage = GarageManager;

