/* =============================================
   HRz PITSTOP – Dynamic SEO & JSON-LD Structured Data Engine
   ============================================= */

window.HRz = window.HRz || {};

class SEOService {
  static updateSEOForView(viewName, data = {}) {
    this.updateCanonicalURL(viewName, data);
    this.updateTitleAndDescription(viewName, data);
    this.injectJSONLD(viewName, data);
  }

  static _defaultTitle = null;
  static _defaultDescription = null;

  // Current catalog params from the hash URL (category/sort/search/
  // subcategory/brand). App passes only the route to SEO, so params must
  // be read here, not from `data`.
  static _catalogParams() {
    try {
      const raw = (window.location.hash || "").replace(/^#/, "");
      const [, queryString] = raw.split("?");
      const params = new URLSearchParams(queryString || "");
      return {
        category: params.get("category"),
        subcategory: params.get("subcategory"),
        search: params.get("search"),
        sort: params.get("sort"),
        brand: params.get("brand")
      };
    } catch (e) {
      return {};
    }
  }

  static _resolveDisplayCategory(raw) {
    if (!raw) return null;
    try {
      if (window.HRz.Catalog && window.HRz.Catalog.resolveCategory) {
        return window.HRz.Catalog.resolveCategory(raw);
      }
    } catch (e) { /* fall through to the local alias map */ }
    const aliases = {
      "protection": "Bike Protection",
      "lights": "Lighting & Electrical",
      "lighting": "Lighting & Electrical",
      "luggage": "Luggage & Touring",
      "touring": "Luggage & Touring",
      "helmets": "Helmets & Accessories",
      "riding-gears": "Riding Gears",
      "riding-gear": "Riding Gears",
      "maintenance": "Cleaning & Care"
    };
    return aliases[String(raw).toLowerCase()] || raw;
  }

  static _deptDisplayName(viewName) {
    const map = {
      "helmets": "Helmets & Accessories",
      "protection": "Bike Protection",
      "crash-guards": "Bike Protection",
      "luggage": "Luggage & Touring",
      "lights": "Lighting & Electrical",
      "lighting": "Lighting & Electrical",
      "riding-gears": "Riding Gears",
      "riding-gear": "Riding Gears",
      "jackets": "Riding Gears",
      "performance": "Performance Accessories",
      "maintenance": "Cleaning & Care"
    };
    return map[viewName] || null;
  }

  // Dynamic title + meta description. Canonical / JSON-LD behaviour is
  // unchanged. Home (and unknown views) restore the page's original
  // title/description, captured on first call, so navigating back home
  // does not leave a product/catalog title behind.
  static updateTitleAndDescription(viewName, data = {}) {
    if (this._defaultTitle === null) {
      this._defaultTitle = document.title || "";
      const meta = document.querySelector('meta[name="description"]');
      this._defaultDescription = meta ? meta.getAttribute("content") : "";
    }
    const setMeta = (content) => {
      let meta = document.querySelector('meta[name="description"]');
      if (!meta) {
        meta = document.createElement("meta");
        meta.setAttribute("name", "description");
        document.head.appendChild(meta);
      }
      meta.setAttribute("content", content);
    };
    const setOg = (content, isTitle) => {
      const prop = isTitle ? 'meta[property="og:title"]' : 'meta[property="og:description"]';
      const el = document.querySelector(prop);
      if (el) el.setAttribute("content", content);
    };

    let title = null;
    let description = null;

    if (viewName === "product" && data.product) {
      const p = data.product;
      title = `${p.name} | HRz Pitstop`;
      const highlights = Array.isArray(p.highlights) && p.highlights.length
        ? p.highlights.join(". ")
        : `${p.name} — ${[p.brand, p.category].filter(Boolean).join(" · ")} at HRz Pitstop.`;
      description = String(highlights).slice(0, 160);
    } else if (viewName === "catalog" || this._deptDisplayName(viewName)) {
      const params = this._catalogParams();
      const category = this._resolveDisplayCategory(params.category)
        || (viewName === "catalog" ? null : this._deptDisplayName(viewName));
      const parts = [];
      if (params.search) parts.push(`Search: "${params.search}"`);
      if (category && category !== "All") parts.push(category);
      if (params.subcategory && params.subcategory !== "All") parts.push(params.subcategory);
      if (params.brand) parts.push(params.brand);
      const label = parts.length ? parts.join(" — ") : "Product Catalog";
      const sortLabels = (window.HRz.Utils && window.HRz.Utils.SORT_LABELS) || {};
      const sortSuffix = params.sort && params.sort !== "featured" && sortLabels[params.sort]
        ? ` (${sortLabels[params.sort]})` : "";
      title = `${label}${sortSuffix} | HRz Pitstop`;
      description = `Shop ${parts.length ? parts.join(", ") : "motorcycle accessories and riding gear"} at HRz Pitstop.${sortSuffix ? ` Sorted by ${sortLabels[params.sort]}.` : ""}`;
    } else if (viewName === "home" || viewName === "" || !viewName) {
      title = this._defaultTitle;
      description = this._defaultDescription;
    }

    if (title) {
      document.title = title;
      setOg(title, true);
    }
    if (description) {
      setMeta(description);
      setOg(description, false);
    }
  }

  static updateCanonicalURL(viewName, data = {}) {
    let canonical = document.querySelector("link[rel='canonical']");
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }

    const baseURL = window.location.origin + window.location.pathname;
    let url = baseURL;
    if (viewName === "product" && data.product) {
      url = `${baseURL}?view=product&id=${data.product.id}`;
    } else if (viewName !== "home") {
      url = `${baseURL}?view=${viewName}`;
    }
    canonical.setAttribute("href", url);
  }

  static injectJSONLD(viewName, data = {}) {
    const existingScript = document.getElementById("dynamic-jsonld");
    if (existingScript) existingScript.remove();

    const schemas = [];

    schemas.push({
      "@context": "https://schema.org",
      "@type": "MotorcycleStore",
      "name": "HRz Pitstop",
      "url": window.location.origin,
      "logo": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%23e63946'/><text x='50' y='68' font-size='52' font-weight='900' text-anchor='middle' fill='white' font-family='sans-serif'>HRz</text></svg>",
      "description": "India's #1 Motorcycle Accessories & Riding Gear Store with Verified Fitment Guarantee.",
      "telephone": "+91 98765 43210",
      "priceRange": "₹₹",
      "address": {
        "@type": "PostalAddress",
        "addressLocality": "Bengaluru",
        "addressRegion": "Karnataka",
        "addressCountry": "IN"
      }
    });

    const breadcrumbItems = [
      { "@type": "ListItem", "position": 1, "name": "Home", "item": window.location.origin }
    ];

    if (viewName === "catalog" || this._deptDisplayName(viewName)) {
      breadcrumbItems.push({ "@type": "ListItem", "position": 2, "name": "Catalog", "item": `${window.location.origin}/#catalog` });
      // Extra breadcrumb for the active catalog params (category/search/
      // brand) — additive only; existing items are unchanged.
      const params = this._catalogParams();
      const catLabel = this._resolveDisplayCategory(params.category)
        || (viewName === "catalog" ? null : this._deptDisplayName(viewName));
      const detailLabel = params.search ? `Search: ${params.search}`
        : (catLabel && catLabel !== "All" ? catLabel : (params.brand || null));
      if (detailLabel) {
        breadcrumbItems.push({ "@type": "ListItem", "position": 3, "name": detailLabel, "item": window.location.href });
      }
    } else if (viewName === "product" && data.product) {
      breadcrumbItems.push({ "@type": "ListItem", "position": 2, "name": "Catalog", "item": `${window.location.origin}/#catalog` });
      breadcrumbItems.push({ "@type": "ListItem", "position": 3, "name": data.product.name, "item": `${window.location.origin}/#product?id=${data.product.id}` });
      
      schemas.push({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": data.product.name,
        "image": [data.product.image],
        "description": data.product.highlights ? data.product.highlights.join(". ") : data.product.name,
        "sku": data.product.sku,
        "brand": {
          "@type": "Brand",
          "name": "HRz Pitstop"
        },
        "offers": {
          "@type": "Offer",
          "url": window.location.href,
          "priceCurrency": "INR",
          "price": data.product.price,
          "priceValidUntil": "2027-12-31",
          "itemCondition": "https://schema.org/NewCondition",
          "availability": data.product.inStock ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
          "seller": {
            "@type": "Organization",
            "name": "HRz Pitstop"
          }
        },
        "aggregateRating": {
          "@type": "AggregateRating",
          "ratingValue": data.product.rating || "4.9",
          "reviewCount": data.product.reviewCount || "150"
        }
      });
    }

    schemas.push({
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": breadcrumbItems
    });

    const script = document.createElement("script");
    script.id = "dynamic-jsonld";
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(schemas, null, 2);
    document.head.appendChild(script);
  }
}

window.HRz.SEO = SEOService;
