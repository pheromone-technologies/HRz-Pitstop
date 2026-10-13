import os

file_path = "e:\\coad\\hrx website 2\\js\\app.js"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject models route
old_route = """    switch (route) {
      case "home":
        this.renderHomeView(activeViewEl);
        break;
      case "catalog":"""
new_route = """    switch (route) {
      case "home":
        this.renderHomeView(activeViewEl);
        break;
      case "models":
        this.renderModelsView(activeViewEl, params.get("brand"));
        break;
      case "catalog":"""

content = content.replace(old_route, new_route)

# 2. Update renderHomeView bike selector
old_selector = """      <!-- 3D Bike Selector -->
      <section class="bike-selector-3d section" id="bikeSelector3D">
        <div class="section-head">
          <div><p class="eyebrow red">Select your machine</p><h2>CHOOSE YOUR <em>RIDE</em></h2></div>
        </div>
        <div class="bike-slider-container">
          <div class="bike-slider">
            ${(() => {
              const allBikes = window.HRz.DB.getBikes();
              // Pick diverse bikes: one per brand, then fill remaining
              const seenBrands = new Set();
              const diverseBikes = [];
              // Priority brand order for visual variety
              const brandOrder = ['Royal Enfield', 'KTM', 'BMW', 'Triumph', 'Yamaha', 'TVS', 'Honda', 'Bajaj', 'Kawasaki', 'Suzuki', 'Hero'];
              for (const brand of brandOrder) {
                const bike = allBikes.find(b => b.brand === brand && !seenBrands.has(b.brand));
                if (bike) { diverseBikes.push(bike); seenBrands.add(bike.brand); }
                if (diverseBikes.length >= 7) break;
              }
              // If less than 7, fill with remaining bikes
              for (const bike of allBikes) {
                if (diverseBikes.length >= 7) break;
                if (!diverseBikes.some(b => b.id === bike.id)) diverseBikes.push(bike);
              }
              const bikeImages = ['bike_t_1.webp','bike_t_2.webp','bike_t_3.webp','bike_t_4.webp','bike_t_5.webp','bike_t_6.webp','bike_t_7.webp'];
              return [1, 2, 3].map(set => diverseBikes.map((bike, idx) => `
                <div class="bike-item ${set === 2 && idx === 2 ? 'active' : ''}" data-brand="${bike.brand}" data-model="${bike.model}" data-variant="${bike.variant}" data-year="${bike.year}">
                  <div class="bike-img-wrap"><img src="images/${bikeImages[idx % 7]}" alt="${bike.brand} ${bike.model}" /></div>
                  <div class="bike-info"><h3>${bike.model}</h3></div>
                </div>
              `).join('')).join('');
            })()}
          </div>
        </div>
      </section>"""

new_selector = """      <!-- 3D Bike Selector -->
      <section class="bike-selector-3d section" id="bikeSelector3D">
        <div class="section-head">
          <div><p class="eyebrow red">Select your machine</p><h2>CHOOSE YOUR <em>BRAND</em></h2></div>
        </div>
        <div class="bike-slider-container">
          <div class="bike-slider">
            ${(() => {
              const brands = Object.keys(window.HRz.Menu.menuData.shopByBike);
              const brandImages = ['bike_t_1.webp','bike_t_2.webp','bike_t_3.webp','bike_t_4.webp','bike_t_5.webp','bike_t_6.webp','bike_t_7.webp'];
              return [1, 2, 3].map(set => brands.map((brand, idx) => `
                <div class="bike-item" style="cursor:pointer;" onclick="window.location.hash='#models?brand=' + encodeURIComponent('${brand}')">
                  <div class="bike-img-wrap"><img src="images/${brandImages[idx % 7]}" alt="${brand}" /></div>
                  <div class="bike-info"><h3>${brand}</h3></div>
                </div>
              `).join('')).join('');
            })()}
          </div>
        </div>
      </section>"""

content = content.replace(old_selector, new_selector)

# 3. Append renderModelsView method to App class
models_view_code = """
  static renderModelsView(container, brand) {
    if (!brand) {
      window.location.hash = "#home";
      return;
    }
    const models = window.HRz.Menu.menuData.shopByBike[brand] || [];
    const brandImages = ['bike_t_1.webp','bike_t_2.webp','bike_t_3.webp','bike_t_4.webp','bike_t_5.webp','bike_t_6.webp','bike_t_7.webp'];
    
    container.innerHTML = `
      <div class="section-head" style="margin-top:40px; text-align:center;">
        <div><p class="eyebrow red">${brand}</p><h2>SELECT YOUR <em>MODEL</em></h2></div>
      </div>
      <div class="shop-grid" style="padding: 20px 4vw;">
        ${models.map((model, idx) => `
          <div class="product-card" style="cursor:pointer;" onclick="window.location.hash='#catalog?search=' + encodeURIComponent('${model}')">
            <div class="product-img">
              <img src="images/${brandImages[idx % 7]}" alt="${model}" />
            </div>
            <div class="product-info" style="text-align:center;">
              <h3 class="product-title" style="margin:10px 0;">${model}</h3>
              <button class="button button-red" style="width:100%; margin-top:10px;">View Accessories</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }
}
"""

if "renderModelsView" not in content:
    # Replace the last `}` closing the App class
    content = content.rsplit("}", 1)
    content = content[0] + models_view_code

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated app.js successfully!")
