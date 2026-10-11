/* =============================================
   HRz PITSTOP – Normalized Database & Simulated API Service
   Decoupled Products, Bikes, Compatibility & CMS Operations
   ============================================= */

window.HRz = window.HRz || {};

const CACHE_KEYS = {
  BIKES: "hrz_db_bikes_v20",
  PRODUCTS: "hrz_db_products_v20",
  COMPATIBILITY: "hrz_db_compatibility_v20",
  REVIEWS: "hrz_db_reviews_v20",
  ORDERS: "hrz_db_orders_v20",
  BUNDLES: "hrz_db_bundles_v20"
};

const DEFAULT_BIKES = [
  { "id": "bike-re-him-450-adv", "brand": "Royal Enfield", "model": "Himalayan 450", "year": 2024, "variant": "450 Adventure", "engineCc": 452, "category": "Adventure", "region": "Global" },
  { "id": "bike-re-him-450-sum", "brand": "Royal Enfield", "model": "Himalayan 450", "year": 2024, "variant": "450 Summit", "engineCc": 452, "category": "Adventure", "region": "Global" },
  { "id": "bike-re-him-411", "brand": "Royal Enfield", "model": "Himalayan 411", "year": 2023, "variant": "411 Base", "engineCc": 411, "category": "Adventure", "region": "Global" },
  { "id": "bike-re-him-411-scram", "brand": "Royal Enfield", "model": "Scram 411", "year": 2023, "variant": "411 Base", "engineCc": 411, "category": "Scrambler", "region": "Global" },
  { "id": "bike-re-hun-350-met", "brand": "Royal Enfield", "model": "Hunter 350", "year": 2024, "variant": "350 Metro", "engineCc": 349, "category": "Roadster", "region": "Global" },
  { "id": "bike-re-cla-350-reb", "brand": "Royal Enfield", "model": "Classic 350 Reborn", "year": 2024, "variant": "350 Reborn", "engineCc": 349, "category": "Classic", "region": "Global" },
  { "id": "bike-re-met-350-ste", "brand": "Royal Enfield", "model": "Meteor 350", "year": 2024, "variant": "350 Stellar", "engineCc": 349, "category": "Cruiser", "region": "Global" },
  { "id": "bike-re-int-650-twi", "brand": "Royal Enfield", "model": "Interceptor 650", "year": 2024, "variant": "650 Twin", "engineCc": 648, "category": "Twin", "region": "Global" },
  { "id": "bike-re-gt-650-ape", "brand": "Royal Enfield", "model": "Continental GT 650", "year": 2024, "variant": "650 Apex Grey", "engineCc": 648, "category": "Cafe Racer", "region": "Global" },
  { "id": "bike-re-sm-650-ast", "brand": "Royal Enfield", "model": "Super Meteor 650", "year": 2024, "variant": "650 Astral", "engineCc": 648, "category": "Cruiser", "region": "Global" },
  { "id": "bike-re-gue-450-ana", "brand": "Royal Enfield", "model": "Guerrilla 450", "year": 2024, "variant": "450 Analogue", "engineCc": 452, "category": "Roadster", "region": "Global" },
  { "id": "bike-ktm-duke-390-g3", "brand": "KTM", "model": "Duke 390 Gen-3", "year": 2024, "variant": "Gen-3 Standard", "engineCc": 399, "category": "Naked", "region": "India" },
  { "id": "bike-yam-mt15-v2", "brand": "Yamaha", "model": "MT-15 V2", "year": 2024, "variant": "V2 Deluxe", "engineCc": 155, "category": "Naked", "region": "India" },
  { "id": "bike-tvs-apc-rr310", "brand": "TVS", "model": "Apache RR 310", "year": 2024, "variant": "RR310 BTO", "engineCc": 312, "category": "Supersport", "region": "India" },
  { "id": "bike-hnd-cb350-pro", "brand": "Honda", "model": "H'ness CB 350", "year": 2024, "variant": "DLX Pro", "engineCc": 348, "category": "Classic", "region": "India" },
  { "id": "bike-baj-dom-400", "brand": "Bajaj", "model": "Dominar 400", "year": 2024, "variant": "400 Touring Factory", "engineCc": 373, "category": "Tourer", "region": "India" },
  { "id": "bike-bmw-g310-gs", "brand": "BMW", "model": "G 310 GS", "year": 2024, "variant": "GS Adventure", "engineCc": 313, "category": "Adventure", "region": "Global" },
  { "id": "bike-tri-spd-400", "brand": "Triumph", "model": "Speed 400", "year": 2024, "variant": "400 Roadster", "engineCc": 398, "category": "Roadster", "region": "Global" }
];

const DEFAULT_PRODUCTS = [
  {
    "id": "axor-helmet",
    "name": "Axor Apex Carbon Full Face Helmet",
    "category": "Helmets",
    "price": 4999,
    "originalPrice": 5999,
    "image": "images/helmet_product.webp",
    "gallery": ["images/helmet_product.webp", "images/category_helmets.webp"],
    "rating": 4.9,
    "authenticity": "ECE & DOT Certified",
    "warranty": "24 months",
    "reviewCount": 184,
    "ridersInstalled": 92,
    "badge": "BESTSELLER",
    "inStock": true,
    "sku": "HRZ-HLM-01",
    "highlights": ["Carbon fiber finish with aerodynamic spoiler", "Dual visor system with Pinlock 30 anti-fog lens", "Intercom slot ready for Bluetooth modules", "Weight: 1,350g — Ultralight build"]
  },
  {
    "id": "crash-guard-steelmoto",
    "name": "HRz Expedition Heavy Engine Crash Guard",
    "category": "Protection",
    "price": 3899,
    "originalPrice": 4499,
    "image": "images/crash_guard_product.webp",
    "gallery": ["images/crash_guard_product.webp", "images/category_protection.webp"],
    "rating": 4.8,
    "authenticity": "OEM Custom Engineered",
    "warranty": "36 months",
    "reviewCount": 142,
    "ridersInstalled": 78,
    "badge": "HEAVY DUTY",
    "inStock": true,
    "sku": "HRZ-CG-HIM450",
    "highlights": ["Seamless cold-drawn steel tube construction", "Replaceable CNC slider bobbins included", "Direct chassis mounting with zero vibration", "Powder coated for corrosion resistance"]
  },
  {
    "id": "fog-lights-led",
    "name": "HyperBeam 60W Dual LED Fog Light Kit",
    "category": "Lights",
    "price": 3299,
    "originalPrice": 4299,
    "image": "images/fog_lights_product.webp",
    "gallery": ["images/fog_lights_product.webp", "images/category_lights.webp"],
    "rating": 4.9,
    "authenticity": "IP68 Waterproof Standard",
    "warranty": "12 months",
    "reviewCount": 210,
    "ridersInstalled": 134,
    "badge": "HIGH LUMEN",
    "inStock": true,
    "sku": "HRZ-FL-60W",
    "highlights": ["6000 lumens dual beam (Yellow Amber + White High)", "Aircraft grade CNC aluminum housing", "Plug-and-play wiring harness with waterproof switch", "Universal handlebar clamp included"]
  },
  {
    "id": "saddlebags-touring",
    "name": "HRz Overland 40L Waterproof Saddlebags",
    "category": "Luggage",
    "price": 4599,
    "originalPrice": 5299,
    "image": "images/saddlebags_product.webp",
    "gallery": ["images/saddlebags_product.webp", "images/category_luggage.webp"],
    "rating": 4.7,
    "authenticity": "1000D TPU Roll-top",
    "warranty": "24 months",
    "reviewCount": 96,
    "ridersInstalled": 61,
    "badge": "EXPEDITION READY",
    "inStock": true,
    "sku": "HRZ-LU-40L",
    "highlights": ["100% waterproof seam-welded construction", "40 liters combined total capacity (20L x 2)", "Quick-release heavy duty strap mounting", "Reflective high-visibility accents"]
  },
  {
    "id": "brake-pads-ceramic",
    "name": "Brembo High Performance Ceramic Brake Pads",
    "category": "Protection",
    "price": 1899,
    "originalPrice": 2299,
    "image": "images/bash_plate_product.webp",
    "gallery": ["images/bash_plate_product.webp"],
    "rating": 4.9,
    "authenticity": "100% Original Brembo Italy",
    "warranty": "6 months",
    "reviewCount": 320,
    "ridersInstalled": 195,
    "badge": "OEM GRADE",
    "inStock": true,
    "sku": "HRZ-BP-BRM",
    "highlights": ["Zero fade braking even under aggressive track use", "Low dust & rotor-friendly organic ceramic formulation", "Includes anti-squeal shims", "Direct fitment replacement"]
  },
  {
    "id": "windshield-adventure",
    "name": "HRz Touring Windscreen & Intercom Kit",
    "category": "Touring",
    "price": 2499,
    "originalPrice": 2999,
    "image": "images/intercom_product.webp",
    "gallery": ["images/intercom_product.webp"],
    "rating": 4.6,
    "authenticity": "PMMA High Impact Polycarbonate",
    "warranty": "12 months",
    "reviewCount": 75,
    "ridersInstalled": 44,
    "badge": "HIGH WIND PROTECTION",
    "inStock": true,
    "sku": "HRZ-WS-CL",
    "highlights": ["Reduces chest windblast at highway speeds", "UV resistant optically clear material", "Zero buffeting aerodynamic curve", "Uses OEM mounting points"]
  }
];

const DEFAULT_COMPATIBILITY = [
  { "id": "cmp-1", "productId": "axor-helmet", "bikeId": "bike-re-him-450-adv", "fitType": "Universal", "notes": "Fits all riders", "sku": "HRZ-HLM-UNI" },
  { "id": "cmp-2", "productId": "axor-helmet", "bikeId": "bike-ktm-duke-390-g3", "fitType": "Universal", "notes": "Fits all riders", "sku": "HRZ-HLM-UNI" },
  { "id": "cmp-3", "productId": "axor-helmet", "bikeId": "bike-yam-mt15-v2", "fitType": "Universal", "notes": "Fits all riders", "sku": "HRZ-HLM-UNI" },
  { "id": "cmp-4", "productId": "axor-helmet", "bikeId": "bike-tri-spd-400", "fitType": "Universal", "notes": "Fits all riders", "sku": "HRZ-HLM-UNI" },
  { "id": "cmp-6", "productId": "crash-guard-steelmoto", "bikeId": "bike-re-him-450-adv", "fitType": "OEM Fit", "notes": "Direct chassis mount with stock bolts", "sku": "HRZ-CG-HIM450" },
  { "id": "cmp-8", "productId": "crash-guard-steelmoto", "bikeId": "bike-baj-dom-400", "fitType": "OEM Fit", "notes": "Custom bracket kit included for Dominar frame", "sku": "HRZ-CG-DOM400" },
  { "id": "cmp-10", "productId": "fog-lights-led", "bikeId": "bike-re-him-450-adv", "fitType": "Universal", "notes": "Mounts on crash guard tube (22mm-28mm)", "sku": "HRZ-FL-60W" },
  { "id": "cmp-12", "productId": "fog-lights-led", "bikeId": "bike-bmw-g310-gs", "fitType": "Universal", "notes": "Mounts on crash guard or auxiliary light bar", "sku": "HRZ-FL-60W" },
  { "id": "cmp-14", "productId": "saddlebags-touring", "bikeId": "bike-re-him-450-adv", "fitType": "OEM Fit", "notes": "Straps over pillion seat", "sku": "HRZ-LU-40L" },
  { "id": "cmp-17", "productId": "brake-pads-ceramic", "bikeId": "bike-ktm-duke-390-g3", "fitType": "OEM Fit", "notes": "Front caliper replacement for ByBre 4-piston", "sku": "HRZ-BP-KTM390" },
  { "id": "cmp-20", "productId": "windshield-adventure", "bikeId": "bike-re-him-450-adv", "fitType": "OEM Fit", "notes": "Replaces OEM short visor using stock screws", "sku": "HRZ-WS-HIM450" }
];

const DEFAULT_REVIEWS = [
  {
    "id": "rev-101",
    "productId": "crash-guard-steelmoto",
    "bikeName": "Royal Enfield Himalayan 450 Adventure",
    "reviewerName": "Vikramaditya S.",
    "rating": 5,
    "date": "2026-06-14",
    "title": "Saved my engine during a low-speed slide in Leh!",
    "comment": "Installed this before my Ladakh trip. Took a spill on slush near Zoji La. Guard took the full impact, not a scratch on the engine casing or tank! Worth every single rupee.",
    "verifiedFitment": true,
    "photo": "images/crash_guard_product.webp",
    "status": "published"
  },
  {
    "id": "rev-102",
    "productId": "fog-lights-led",
    "bikeName": "BMW G310 GS Adventure",
    "reviewerName": "Rohan D.",
    "rating": 5,
    "date": "2026-07-02",
    "title": "Night visibility upgraded tenfold!",
    "comment": "Cruising through Western Ghats fog with yellow beam on is an absolute game-changer.",
    "verifiedFitment": true,
    "photo": "images/fog_lights_product.webp",
    "status": "published"
  }
];

const DEFAULT_ORDERS = [
  {
    "id": "HRZ-ORD-98421",
    "date": "2026-07-20",
    "bike": "Royal Enfield Himalayan 450 Adventure (2024)",
    "status": "In Transit",
    "trackingId": "DTDC-IN-889123",
    "items": [
      { "productId": "crash-guard-steelmoto", "name": "HRz Expedition Heavy Engine Crash Guard", "price": 3899, "quantity": 1, "image": "images/crash_guard_product.webp", "sku": "HRZ-CG-01" }
    ],
    "total": 3899,
    "paymentMethod": "UPI GPay",
    "shippingAddress": "Plot 42, HSR Layout, Sector 3, Bengaluru, Karnataka - 560102"
  }
];

const DEFAULT_BUNDLES = [
  {
    "id": "monsoon-protection-kit",
    "name": "Monsoon Rider Protection Kit",
    "description": "Essential weatherproof gear, IP68 LED fog lights, and high-traction ceramic brake pads for heavy downpours.",
    "price": 8999,
    "originalPrice": 10999,
    "discountPercent": 18,
    "badge": "WEATHERPROOF",
    "items": ["fog-lights-led", "saddlebags-touring", "brake-pads-ceramic"]
  },
  {
    "id": "expedition-ladakh-kit",
    "name": "Leh-Ladakh Expedition Pack",
    "description": "Maximum chassis protection, 40L waterproof luggage, windshield, and auxiliary fog illumination.",
    "price": 12999,
    "originalPrice": 15697,
    "discountPercent": 17,
    "badge": "BEST VALUE",
    "items": ["crash-guard-steelmoto", "saddlebags-touring", "fog-lights-led", "windshield-adventure"]
  }
];

const DEMO_PRODUCT_GROUPS = [
  {
    category: "Helmets",
    image: "images/category_helmets.webp",
    prefix: "Demo Helmet",
    gallery: ["images/helmet_product.webp", "images/intercom_product.webp", "images/category_helmets.webp"],
    fitmentCategories: ["Adventure", "Roadster", "Classic", "Naked", "Supersport", "Tourer", "Cruiser", "Scrambler", "Twin", "Cafe Racer"]
  },
  {
    category: "Protection",
    image: "images/category_protection.webp",
    prefix: "Demo Protection",
    gallery: ["images/crash_guard_product.webp", "images/bash_plate_product.webp", "images/category_protection.webp"],
    fitmentCategories: ["Adventure", "Roadster", "Classic", "Naked", "Supersport", "Tourer", "Cruiser", "Scrambler", "Twin", "Cafe Racer"]
  },
  {
    category: "Lights",
    image: "images/category_lights.webp",
    prefix: "Demo Light",
    gallery: ["images/fog_lights_product.webp", "images/phone_mount_product.webp", "images/category_lights.webp"],
    fitmentCategories: ["Adventure", "Roadster", "Naked", "Tourer", "Cruiser", "Scrambler"]
  },
  {
    category: "Luggage",
    image: "images/category_luggage.webp",
    prefix: "Demo Luggage",
    gallery: ["images/saddlebags_product.webp", "images/phone_mount_product.webp", "images/category_luggage.webp"],
    fitmentCategories: ["Adventure", "Tourer", "Cruiser", "Classic", "Roadster"]
  },
  {
    category: "Touring",
    image: "images/category_touring.webp",
    prefix: "Demo Touring",
    gallery: ["images/intercom_product.webp", "images/helmet_product.webp", "images/category_touring.webp"],
    fitmentCategories: ["Adventure", "Tourer", "Cruiser", "Classic", "Roadster", "Naked"]
  }
];

function buildDemoProducts() {
  return [];
}

class DBService {
  static bikes = [];
  static products = [];
  static compatibility = [];
  static reviews = [];
  static orders = [];
  static bundles = [];
  static initialized = false;
  static loadError = null;

  static async init() {
    if (this.initialized) return;

    try {
      if (window.HRz.Storage?.cleanupLegacyKeys) {
        window.HRz.Storage.cleanupLegacyKeys([...Object.values(CACHE_KEYS), "hrz_db_bikes_v16", "hrz_db_products_v16", "hrz_db_compatibility_v16", "hrz_db_reviews_v16", "hrz_db_orders_v16", "hrz_db_bundles_v16", "hrz-pitstop-state-v6", "hrz_db_bikes_v7", "hrz_db_products_v7", "hrz_db_compatibility_v7", "hrz_db_reviews_v7", "hrz_db_orders_v7", "hrz_db_bundles_v7"]);
      }

      const cachedBikes = localStorage.getItem(CACHE_KEYS.BIKES);
      const cachedProducts = localStorage.getItem(CACHE_KEYS.PRODUCTS);
      const cachedComp = localStorage.getItem(CACHE_KEYS.COMPATIBILITY);
      const cachedReviews = localStorage.getItem(CACHE_KEYS.REVIEWS);
      const cachedOrders = localStorage.getItem(CACHE_KEYS.ORDERS);
      const cachedBundles = localStorage.getItem(CACHE_KEYS.BUNDLES);

      if (cachedBikes && cachedProducts && cachedComp) {
        this.bikes = JSON.parse(cachedBikes);
        this.products = JSON.parse(cachedProducts);
        this.compatibility = JSON.parse(cachedComp);
        this.reviews = cachedReviews ? JSON.parse(cachedReviews) : DEFAULT_REVIEWS;
        this.orders = cachedOrders ? JSON.parse(cachedOrders) : DEFAULT_ORDERS;
        this.bundles = cachedBundles ? JSON.parse(cachedBundles) : DEFAULT_BUNDLES;
      } else {
        try {
          const [bRes, pRes, cRes, rRes, oRes, bdRes] = await Promise.all([
            fetch("data/bikes.json").then(r => r.json()),
            fetch("data/products.json").then(r => r.json()),
            fetch("data/compatibility.json").then(r => r.json()),
            fetch("data/reviews.json").then(r => r.json()),
            fetch("data/orders.json").then(r => r.json()),
            fetch("data/bundles.json").then(r => r.json())
          ]);

          this.bikes = bRes;
          this.products = pRes;
          this.compatibility = cRes;
          this.reviews = rRes;
          this.orders = oRes;
          this.bundles = bdRes;
          this.loadError = null;
        } catch (fetchErr) {
          this.loadError = {
            message: "Unable to load the dataset. Serve this site over http://localhost instead of opening index.html with file://.",
            details: fetchErr
          };
          if (window.HRz && window.HRz.Utils && window.HRz.Utils.showToast) {
            window.HRz.Utils.showToast("Failed to load product data! If you opened this via file://, you must use a local server instead.", "error");
          }
          this.bikes = [];
          this.products = [];
          this.compatibility = [];
          this.reviews = [];
          this.orders = [];
          this.bundles = [];
        }
      }

      // this.products = [...this.products, ...buildDemoProducts().filter(demo => !this.products.some(p => p.id === demo.id))];

      if (!this.compatibility.length) {
        this.compatibility = [];
      }

      this._persist();
      this.initialized = true;
    } catch (err) {
      console.error("DB Init error:", err);
      this.loadError = {
        message: "Database initialization failed. Check the browser console and run the site from a local HTTP server.",
        details: err
      };
      this.bikes = [];
      this.products = [];
      this.compatibility = [];
      this.reviews = [];
      this.orders = [];
      this.bundles = [];
      this.initialized = true;
    }
  }

  static _persist() {
    try {
      localStorage.setItem(CACHE_KEYS.BIKES, JSON.stringify(this.bikes));
      // PRODUCTS array is too large (~11MB), do not save to localStorage
      localStorage.setItem(CACHE_KEYS.COMPATIBILITY, JSON.stringify(this.compatibility));
      localStorage.setItem(CACHE_KEYS.REVIEWS, JSON.stringify(this.reviews));
      localStorage.setItem(CACHE_KEYS.ORDERS, JSON.stringify(this.orders));
      localStorage.setItem(CACHE_KEYS.BUNDLES, JSON.stringify(this.bundles));
    } catch (e) {
      console.warn("LocalStorage persist error:", e);
      window.HRz?.Utils?.showToast("Could not save the database cache. The browser storage quota may be full.", "error");
    }
  }

  static getBikes() { return this.bikes; }
  static getProducts() { return this.products; }
  static getProductById(id) { return this.products.find(p => p.id === id) || null; }
  static getCompatibility() { return this.compatibility; }
  static getBundles() { return this.bundles; }
  static getReviews() { return this.reviews; }
  static getOrders() { return this.orders; }

  static getCategories() {
    const cats = new Set();
    this.products.forEach(p => { if (p.category) cats.add(p.category); });
    return Array.from(cats).sort();
  }

  static checkFitment(productId, activeBike) {
    if (!activeBike) return null;

    const product = this.getProductById(productId);
    
    // 1. Manufacturer Confirmed Fit (from scraped raw data)
    if (product?.bike_compatibility && product.bike_compatibility.length > 0) {
      const activeBikeStr = `${activeBike.brand} ${activeBike.model} ${activeBike.variant || ''}`.toLowerCase().trim();
      const activeBikeStrShort = `${activeBike.brand} ${activeBike.model}`.toLowerCase();
      const activeModelOnly = activeBike.model.toLowerCase();
      
      const isCompat = product.bike_compatibility.some(compatStr => {
         const lower = compatStr.toLowerCase();
         return activeBikeStr.includes(lower) || lower.includes(activeBikeStr) || 
                activeBikeStrShort.includes(lower) || lower.includes(activeBikeStrShort) ||
                lower === activeModelOnly ||
                (lower.includes(activeBike.brand.toLowerCase()) && lower.includes(activeModelOnly));
      });

      if (isCompat) {
        return {
          isCompatible: true,
          fitType: "Manufacturer Confirmed",
          notes: `Verified exact fitment from manufacturer data for ${activeBike.brand} ${activeBike.model}.`,
          sku: product.sku || "HRZ-FIT"
        };
      }
    }

    // 2. Legacy Manual Compatibility Rules (from compatibility.json)
    const matchedBike = this.bikes.find(b =>
      b.brand.toLowerCase() === activeBike.brand.toLowerCase() &&
      b.model.toLowerCase() === activeBike.model.toLowerCase() &&
      (activeBike.variant ? b.variant.toLowerCase().includes(activeBike.variant.toLowerCase()) || activeBike.variant.toLowerCase().includes(b.variant.toLowerCase()) : true)
    );

    const rule = this.compatibility.find(c =>
      c.productId === productId &&
      (matchedBike ? c.bikeId === matchedBike.id : false)
    );

    if (rule) {
      return {
        isCompatible: true,
        fitType: rule.fitType || "OEM Fit",
        notes: rule.notes || "Verified exact chassis fitment",
        sku: rule.sku || "HRZ-FIT"
      };
    }

    const universalRule = this.compatibility.find(c => c.productId === productId && c.fitType === "Universal");
    if (universalRule) {
      return {
        isCompatible: true,
        fitType: "Universal Fit",
        notes: "Compatible with standard motorcycle mounts",
        sku: universalRule.sku
      };
    }
    
    // 3. If it's a bike-specific part (like Bike Protection or Accessories) and it didn't match above, it's NOT compatible.
    const bikeSpecificCats = ["Protection", "Lights", "Accessories"];
    if (bikeSpecificCats.includes(product?.category)) {
       // Only allow if it had a specific rule (which it didn't, since it reached here)
       return null; 
    }

    // 4. Universal Gear / General Fit (Helmets, Gears, etc.)
    if (product?.fitmentCategories?.length && activeBike.category) {
      const activeCategory = activeBike.category.toLowerCase();
      const allowedCategories = product.fitmentCategories.map(c => c.toLowerCase());
      if (allowedCategories.includes(activeCategory)) {
        return {
          isCompatible: true,
          fitType: "Universal Style Match",
          notes: `${product.category} suitable for ${activeBike.category} style riding.`,
          sku: product.sku || "UNI-FIT"
        };
      }
    }

    return null;
  }

  static getProductsForBike(activeBike) {
    const visibleProducts = this.products.filter(p => p.isVisible !== false);
    if (!activeBike) return visibleProducts;
    return visibleProducts.filter(p => this.checkFitment(p.id, activeBike) !== null);
  }

  static getRecommendedProducts(activeBike, excludeId = null, limit = 10) {
    let list = this.getProductsForBike(activeBike);
    if (excludeId) {
      const excludedProduct = this.getProductById(excludeId);
      list = list.filter(p => p.id !== excludeId);
      // When showing related products on a product page, prioritize same category
      if (excludedProduct) {
        const sameCategory = list.filter(p => p.category === excludedProduct.category);
        const otherCategory = list.filter(p => p.category !== excludedProduct.category);
        list = [...sameCategory, ...otherCategory];
      }
    } else if (!activeBike) {
      // On homepage with no bike: show curated selection across categories
      const byCategory = {};
      list.forEach(p => {
        if (!byCategory[p.category]) byCategory[p.category] = [];
        byCategory[p.category].push(p);
      });
      const curated = [];
      const cats = Object.keys(byCategory);
      let idx = 0;
      while (curated.length < limit && idx < 100) {
        const cat = cats[idx % cats.length];
        const catItems = byCategory[cat];
        const pick = catItems.shift();
        if (pick) curated.push(pick);
        idx++;
        if (cats.every(c => byCategory[c].length === 0)) break;
      }
      list = curated;
    }
    return list.slice(0, limit);
  }

  static getCompatibleBikesForProduct(productId) {
    const rules = this.compatibility.filter(c => c.productId === productId);
    return rules.map(rule => {
      const bike = this.bikes.find(b => b.id === rule.bikeId);
      return {
        ruleId: rule.id,
        fitType: rule.fitType,
        notes: rule.notes,
        bike: bike || { brand: "Universal", model: "All Models", variant: "Standard", year: 2024 }
      };
    });
  }

  static markCatalogUnsaved() {
    this.unsavedCatalogChanges = true;
    let banner = document.getElementById('unsaved-catalog-banner');
    if (!banner) {
       banner = document.createElement('div');
       banner.id = 'unsaved-catalog-banner';
       banner.style.cssText = "position:fixed;top:0;left:0;right:0;background:var(--red);color:#fff;text-align:center;padding:12px;z-index:9999;font-weight:bold;box-shadow:0 4px 10px rgba(0,0,0,0.5);";
       banner.innerHTML = "You have unsaved catalog changes — Edit applied in this session only. Click Export JSON and replace data/products.json to make this permanent.";
       document.body.prepend(banner);
    }
  }

  static addProduct(productData) {
    const newId = "prod-" + Date.now();
    const newProduct = {
      id: newId,
      rating: 5.0,
      reviewCount: 0,
      ridersInstalled: 1,
      gallery: [productData.image],
      inStock: true,
      sku: productData.sku || `HRZ-${Date.now().toString().slice(-5)}`,
      ...productData
    };
    this.products.unshift(newProduct);
    this._persist();
    this.markCatalogUnsaved();
    if (window.HRz?.Storage) {
      window.HRz.Storage.addAuditLog(`Added new product "${newProduct.name}" (SKU: ${newProduct.sku})`);
    }
    return newProduct;
  }

  static updateProduct(id, updates) {
    const p = this.getProductById(id);
    if (!p) return null;
    Object.assign(p, updates);
    this._persist();
    this.markCatalogUnsaved();
    if (window.HRz?.Storage) {
      window.HRz.Storage.addAuditLog(`Updated product "${p.name}" details/price (₹${p.price})`);
    }
    return p;
  }

  static deleteProduct(id) {
    const p = this.getProductById(id);
    this.products = this.products.filter(item => item.id !== id);
    this.compatibility = this.compatibility.filter(c => c.productId !== id);
    this._persist();
    this.markCatalogUnsaved();
    if (p && window.HRz?.Storage) {
      window.HRz.Storage.addAuditLog(`Deleted product "${p.name}"`);
    }
  }

  static addCompatibilityRule(productId, bikeId, fitType = "OEM Fit", notes = "") {
    const ruleId = "cmp-" + Date.now();
    const newRule = { id: ruleId, productId, bikeId, fitType, notes };
    this.compatibility.push(newRule);
    this._persist();
    if (window.HRz?.Storage) {
      window.HRz.Storage.addAuditLog(`Created compatibility rule: Product ${productId} <-> Bike ${bikeId}`);
    }
    return newRule;
  }

  static deleteCompatibilityRule(ruleId) {
    this.compatibility = this.compatibility.filter(c => c.id !== ruleId);
    this._persist();
    if (window.HRz?.Storage) {
      window.HRz.Storage.addAuditLog(`Deleted compatibility rule ID ${ruleId}`);
    }
  }

  static updateReviewStatus(reviewId, status) {
    const rev = this.reviews.find(r => r.id === reviewId);
    if (rev) {
      rev.status = status;
      this._persist();
      if (window.HRz?.Storage) {
        window.HRz.Storage.addAuditLog(`Moderated review ${reviewId}: Marked as ${status}`);
      }
    }
  }

  static updateOrderStatus(orderId, status) {
    const ord = this.orders.find(o => o.id === orderId);
    if (ord) {
      ord.status = status;
      this._persist();
      if (window.HRz?.Storage) {
        window.HRz.Storage.addAuditLog(`Updated order ${orderId} status to "${status}"`);
      }
    }
  }

  static exportCompatibilityCSV() {
    let csv = "RuleID,ProductID,ProductName,BikeID,BikeBrand,BikeModel,FitType,Notes\n";
    this.compatibility.forEach(c => {
      const prod = this.getProductById(c.productId);
      const bike = this.bikes.find(b => b.id === c.bikeId);
      const prodName = prod ? `"${prod.name.replace(/"/g, '""')}"` : "Unknown Product";
      const brand = bike ? bike.brand : "Universal";
      const model = bike ? bike.model : "All";
      const notes = c.notes ? `"${c.notes.replace(/"/g, '""')}"` : "";
      csv += `${c.id},${c.productId},${prodName},${c.bikeId},${brand},${model},${c.fitType},${notes}\n`;
    });
    return csv;
  }

  static importCompatibilityCSV(csvContent) {
    if (!window.Papa?.parse) {
      throw new Error("PapaParse is required for CSV import.");
    }

    const parsed = window.Papa.parse(csvContent, {
      header: true,
      skipEmptyLines: true,
      transformHeader: header => header.trim()
    });

    if (parsed.errors?.length) {
      console.warn("CSV parse warnings:", parsed.errors);
    }

    let importedCount = 0;
    const rows = Array.isArray(parsed.data) ? parsed.data : [];

    rows.forEach((row, index) => {
      const getField = (...keys) => {
        for (const key of keys) {
          if (row[key] !== undefined && row[key] !== null) {
            return String(row[key]).trim();
          }
        }
        return "";
      };

      const productId = getField("ProductID", "productId");
      const bikeId = getField("BikeID", "bikeId");
      const fitType = getField("FitType", "fitType") || "OEM Fit";
      const notes = getField("Notes", "notes");
      const ruleIdValue = getField("RuleID", "ruleId");

      if (productId && bikeId) {
        const ruleId = ruleIdValue.startsWith("cmp-") ? ruleIdValue : `cmp-${Date.now()}-${index}`;
        const existing = this.compatibility.find(c => c.productId === productId && c.bikeId === bikeId);
        if (!existing) {
          this.compatibility.push({ id: ruleId, productId, bikeId, fitType, notes });
          importedCount++;
        }
      }
    });

    this._persist();
    if (window.HRz?.Storage) {
      window.HRz.Storage.addAuditLog(`Imported ${importedCount} compatibility rules via CSV`);
    }
    return importedCount;
  }
}

window.HRz.DB = DBService;

