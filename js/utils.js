/* =============================================
   HRz PITSTOP – Shared Utilities & UI Helpers Module
   ============================================= */

window.HRz = window.HRz || {};

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(amount);
}

function renderStarRating(rating) {
  const fullStars = Math.floor(rating);
  const hasHalf = rating % 1 >= 0.5;
  let starsHtml = "";
  for (let i = 0; i < 5; i++) {
    if (i < fullStars) {
      starsHtml += `<span class="star-icon full">★</span>`;
    } else if (i === fullStars && hasHalf) {
      starsHtml += `<span class="star-icon half">★</span>`;
    } else {
      starsHtml += `<span class="star-icon empty">☆</span>`;
    }
  }
  return `<span class="rating-stars">${starsHtml} <strong class="rating-num">${rating.toFixed(1)}</strong></span>`;
}

function showToast(message, type = "info") {
  let toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toastContainer";
    toastContainer.className = "toast-container";
    toastContainer.setAttribute("aria-live", "polite");
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  toast.className = `toast-message toast-${type}`;
  const safeMessage = escapeHTML(String(message));
  toast.innerHTML = `
    <span class="toast-icon">${type === "success" ? "✓" : type === "error" ? "✕" : "ℹ"}</span>
    <span class="toast-text">${safeMessage}</span>
  `;

  toastContainer.appendChild(toast);
  setTimeout(() => toast.classList.add("show"), 10);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function setupModalAccessibility(modalEl, closeCallback) {
  if (!modalEl) return;

  modalEl.setAttribute("role", "dialog");
  modalEl.setAttribute("aria-modal", "true");
  modalEl.setAttribute("tabindex", "-1");

  const focusableElements = modalEl.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (firstElement) firstElement.focus();

  const handleKeyDown = (e) => {
    if (e.key === "Escape") {
      if (closeCallback) closeCallback();
      modalEl.removeEventListener("keydown", handleKeyDown);
    }

    if (e.key === "Tab") {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    }
  };

  modalEl.addEventListener("keydown", handleKeyDown);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function escapeHTML(str) {
  if (!str) return "";
  return String(str).replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}

function levenshtein(a, b) {
  const matrix = [];
  for (let i = 0; i <= b.length; i++) matrix[i] = [i];
  for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1)
        );
      }
    }
  }
  return matrix[b.length][a.length];
}

const STOP_WORDS = new Set(["and", "or", "the", "for", "with", "in", "of", "to", "a", "an", "at", "by", "from", "on", "all", "&"]);

// Normalised key for brand/category matching: lower-case, spaces and
// punctuation stripped, so "MotoTorque" matches the real brand "Moto Torque",
// "STUDDS" matches "Studds", etc. Never invents a brand — it only compares
// values that already exist in the catalogue.
function normalizeKey(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}
function normalizeBrandKey(value) {
  return normalizeKey(value);
}

const SORT_OPTIONS = ["featured", "price-low", "price-high", "rating", "name"];
const SORT_LABELS = {
  "featured": "Featured",
  "price-low": "Price: Low to High",
  "price-high": "Price: High to Low",
  "rating": "Customer Rating",
  "name": "Name: A to Z"
};
function isValidSort(sortBy) {
  return SORT_OPTIONS.includes(sortBy) ? sortBy : "featured";
}

// Identifies accessory/care/film/insert/hardware products that belong to a category
// but should be presented after primary/core items (e.g. helmets before visor inserts).
function isAccessoryProduct(p) {
  if (!p) return false;
  const cat = String(p.category || "").trim();
  const sub = String(p.subcategory || "").trim().toLowerCase();
  const nl = String(p.name || "").trim().toLowerCase();
  const price = Number(p.price) || 0;

  // 1. Helmets & Accessories
  if (cat === "Helmets" || cat === "Helmets & Accessories" || cat.toLowerCase().includes("helmet")) {
    const primaryHelmetSubs = ["full face", "full-face helmet", "open face", "open-face helmet", "modular helmet", "off-road"];

    // Explicit accessory subcategories are ALWAYS accessories
    if (["helmet accessories", "accessories", "riding eyewear", "helmet visor", "visors & spoilers", "visors", "goggles", "eyewear"].includes(sub)) {
      return true;
    }

    // Explicit primary helmet subcategories are core helmets unless they have pure hardware tokens
    if (primaryHelmetSubs.includes(sub)) {
      const hardAccTokens = [
        "pinlock", "insert", "visor mechanism", "pivot kit", "ratchet",
        "cleaner", "spray", "balaclava", "balclava", "chin mount", "chinmount",
        "earphone", "headset", "intercom", "bluetooth", "blutooth", "goggle"
      ];
      if (hardAccTokens.some(t => nl.includes(t))) {
        return true;
      }
      return false;
    }

    // Name tokens for any other items in Helmets & Accessories
    const accTokens = [
      "goggle", "goggles", "balaclava", "balclava", "motomask", "mask", "eyewear",
      "insert", "pinlock", "protector", "film", "screen guard", "tear off", "tear-off",
      "anti fog", "anti-fog", "antifog", "cleaner", "spray", "foam", "chin mount",
      "chinmount", "chin strap", "mobile holder", "helmet lock", "cable lock",
      "fitting", "pivot kit", "ratchet", "mechanism", "base plate", "cheek pad",
      "crown pad", "breath deflector", "chin curtain", "bluetooth", "blutooth", "intercom",
      "communication device", "headset", "earphone", "outer visor", "dark smoke visor",
      "mirror visor", "metal visor", "short visor", "aluminium visor", "full face visor",
      "visor helios", "visor protection", "interior cleaner", "visor clean", "tint with box",
      "tinted visor", "helmet cap", "spoiler"
    ];
    if (accTokens.some(t => nl.includes(t))) return true;
    if (nl.includes("visor") && ["mt 15", "hunter", "guerrilla", "apache", "triumph", "yamaha", "xsr", "hness", "cb200x", "xpulse"].some(b => nl.includes(b))) return true;
    if (nl.startsWith("axor helmets spoiler") || (nl.includes("spoiler") && price < 1500 && !["thunder", "fighter", "typhoon", "raider", "sbh", "ff", "f/f", "apex"].some(m => nl.includes(m)))) return true;
    if (/\bhelmet strap\b/.test(nl) || (/\bstrap\b/.test(nl) && price < 500)) return true;
    return false;
  }

  // 2. Riding Jackets & Apparel / Riding Gears
  if (cat === "Riding Jackets & Apparel" || cat === "Riding Gears" || cat.toLowerCase().includes("riding") || cat.toLowerCase().includes("apparel")) {
    if (["arm sleeves", "socks", "headwear", "headwear & balaclavas", "base layers"].includes(sub)) return true;
    const accTokens = ["sleeve", "socks", "balaclava", "head cap", "mask", "armor", "rain coat", "rainwear", "base layer", "inner"];
    if (accTokens.some(t => nl.includes(t)) && !["jacket", "suit", "pant", "boot"].some(c => nl.includes(c))) return true;
    return false;
  }

  // 3. Boots & Footwear
  if (cat === "Boots & Footwear") {
    if (sub === "boot rain covers") return true;
    if (["gearboot", "shoe cover", "boot cover", "shift protector", "socks", "slider"].some(t => nl.includes(t)) && !["boot", "shoe"].some(c => nl.includes(c))) return true;
    if (nl.includes("gearboot") || (price < 800 && nl.includes("cover"))) return true;
    return false;
  }

  // 4. Luggage & Storage / Luggage & Touring
  if (cat === "Luggage & Storage" || cat === "Luggage & Touring" || cat.toLowerCase().includes("luggage")) {
    const accTokens = ["bungeecord", "bungee cord", "bungee", "bottle holder", "rain cover", "mounting strap"];
    if (accTokens.some(t => nl.includes(t))) return true;
    return false;
  }

  // 5. Lighting & Electrical / Lighting
  if (cat === "Lighting & Electrical" || cat === "Lighting" || cat.toLowerCase().includes("light")) {
    const accTokens = ["clamp", "mount set", "foglight mount", "fog light mount", "mounting bracket", "wire harness", "harness", "dimmer"];
    if (accTokens.some(t => nl.includes(t)) && !["foglight", "fog lamp", "headlight", "bulb", "light"].some(c => nl.includes(c))) return true;
    if (nl.includes("clamp") || nl.includes("mount set") || nl.includes("foglight mount") || nl.includes("fog light mount")) return true;
    return false;
  }

  // 6. Crash Protection / Bike Protection / Guards & Mounts
  if (cat === "Crash Protection" || cat === "Bike Protection" || cat === "Guards & Mounts" || cat.toLowerCase().includes("protection")) {
    if (["+bolts", "+ bolts", "& bolts", "&bolts", "replacement puck", "slider puck", "spare bolt", "bolt kit"].some(k => nl.includes(k))) return true;
    return false;
  }

  // 7. Drive & Transmission
  if (cat === "Drive & Transmission") {
    const accTokens = ["chain lub", "chain lube", "chain clean", "chain paste", "maintenance kit", "care kit", "brush", "brite-o"];
    if (accTokens.some(t => nl.includes(t))) return true;
    return false;
  }

  // 8. Electronics
  if (cat === "Electronics") {
    const accTokens = ["cable", "clamp kit", "mic sponge", "replacement mount", "spacer", "charging cable", "usb cable"];
    if (accTokens.some(t => nl.includes(t)) && !["intercom", "bluetooth", "charger", "holder", "mount pro", "tracker"].some(c => nl.includes(c))) return true;
    return false;
  }

  return false;
}

// Single reusable sort. Never mutates the input array (sorts a decorated
// copy), is stable (original index breaks ties), and guards non-numeric
// prices by sorting them last in both directions. In "featured" mode,
// primary core products are prioritised first, and accessories/care items last.
function sortProducts(products, sortBy) {
  const list = Array.isArray(products) ? [...products] : [];
  const key = isValidSort(sortBy);
  if (key === "featured") {
    const decorated = list.map((p, i) => ({ p, i, acc: isAccessoryProduct(p) ? 1 : 0 }));
    decorated.sort((a, b) => (a.acc - b.acc) || (a.i - b.i));
    return decorated.map(d => d.p);
  }
  const priceNum = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : NaN;
  };
  const decorated = list.map((p, i) => ({ p, i }));
  decorated.sort((a, b) => {
    let cmp = 0;
    if (key === "price-low") {
      const x = priceNum(a.p.price), y = priceNum(b.p.price);
      cmp = (Number.isNaN(x) ? 1 : 0) - (Number.isNaN(y) ? 1 : 0)
        || (Number.isNaN(x) || Number.isNaN(y) ? 0 : x - y);
    } else if (key === "price-high") {
      const x = priceNum(a.p.price), y = priceNum(b.p.price);
      cmp = (Number.isNaN(x) ? 1 : 0) - (Number.isNaN(y) ? 1 : 0)
        || (Number.isNaN(x) || Number.isNaN(y) ? 0 : y - x);
    } else if (key === "rating") {
      cmp = (Number(b.p.rating) || 0) - (Number(a.p.rating) || 0);
    } else if (key === "name") {
      cmp = String(a.p.name || "").localeCompare(String(b.p.name || ""));
    }
    return cmp !== 0 ? cmp : a.i - b.i;
  });
  return decorated.map(d => d.p);
}

// True when the query is a known bike model from bikes.json (e.g.
// "Himalayan 450", "Duke 390 Gen-3"). Such a query can never have an
// exact fitment match in this catalogue (no bike field, no
// bike_compatibility), even if a token like "450" incidentally matches
// product names — so callers must flag it as no-fitment-data.
function looksLikeBikeModel(queryTokens) {
  try {
    const db = window.HRz && window.HRz.DB;
    const bikes = db ? (db.bikes || (db.getBikes ? db.getBikes() : [])) : [];
    if (!bikes || !bikes.length || !queryTokens.length) return false;
    const tokenSet = new Set(queryTokens);
    const modelTokensOf = (s) => String(s || "").toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(t => t.length > 1 && !STOP_WORDS.has(t));
    for (const bike of bikes) {
      const modelTokens = modelTokensOf(bike.model);
      if (!modelTokens.length) continue;
      const brandTokens = modelTokensOf(bike.brand);
      const allModelInQuery = modelTokens.every(t => tokenSet.has(t));
      if (modelTokens.length >= 2 && allModelInQuery) return true;
      if (modelTokens.length === 1 && allModelInQuery
        && brandTokens.some(t => tokenSet.has(t))) return true;
    }
  } catch (e) { /* bike detection is best-effort */ }
  return false;
}

function smartSearch(query, products, activeBike) {
  if (!query) return products;
  
  const rawTokens = String(query).toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(Boolean);
  let tokens = rawTokens.filter(t => t.length > 1 && !STOP_WORDS.has(t));
  if (tokens.length === 0) tokens = rawTokens.filter(t => t.length > 0);
  if (tokens.length === 0) return products;

  const scoredProducts = [];

  for (const p of products) {
    let score = 0;
    const nameStr = (p.name || "").toLowerCase();
    const brandStr = (p.brand || "").toLowerCase();
    const catStr = (p.category || "").toLowerCase();
    const subcatStr = (p.subcategory || "").toLowerCase();
    const skuStr = (p.sku || "").toLowerCase();
    
    const nameWords = nameStr.split(/\s+/);
    const allWords = new Set([...nameWords, ...brandStr.split(/\s+/), ...catStr.split(/\s+/), ...subcatStr.split(/\s+/)]);
    
    let tokensMatched = 0;
    let nameMatches = 0;
    
    for (const token of tokens) {
      const root = (token.endsWith("s") && token.length > 3) ? token.slice(0, -1) : token;
      let bestTokenScore = 0;
      
      // 1. Direct or root word match in product name (highest priority)
      for (const w of nameWords) {
        const wClean = w.replace(/[^a-z0-9]/g, "");
        if (wClean === token || wClean === root) {
          bestTokenScore = Math.max(bestTokenScore, 35);
          nameMatches++;
          break;
        } else if (wClean.startsWith(root) || wClean.startsWith(token)) {
          bestTokenScore = Math.max(bestTokenScore, 24);
          nameMatches++;
          break;
        } else if (token.length >= 4 && wClean.includes(token)) {
          bestTokenScore = Math.max(bestTokenScore, 12);
          nameMatches++;
          break;
        }
      }
      
      // 2. Brand, Category, or Subcategory word match, plus concatenated
      //    forms ("mototorque" vs brand "Moto Torque", "crashprotection").
      if (bestTokenScore === 0) {
        for (const w of allWords) {
          const wClean = w.replace(/[^a-z0-9]/g, "");
          if (wClean === token || wClean === root) {
            bestTokenScore = Math.max(bestTokenScore, 18);
            break;
          } else if (wClean.startsWith(root) || wClean.startsWith(token)) {
            bestTokenScore = Math.max(bestTokenScore, 12);
            break;
          }
        }
      }
      if (bestTokenScore === 0 && token.length >= 3) {
        const tokenNorm = normalizeKey(token);
        const fieldNorms = [normalizeKey(brandStr), normalizeKey(catStr), normalizeKey(subcatStr)];
        if (fieldNorms.some(fn => fn && (fn === tokenNorm || fn.includes(tokenNorm)))) {
          bestTokenScore = Math.max(bestTokenScore, 18);
        }
      }

      // 3. SKU match — but never the placeholder "Missing SKU": 1,464 rows
      //    carry it, so matching it would return almost the whole catalogue
      //    for a query like "missing" or "sku".
      const isPlaceholderSku = !skuStr || skuStr === "missing sku";
      if (!isPlaceholderSku && skuStr.includes(token)) {
        bestTokenScore = Math.max(bestTokenScore, 20);
      }

      // 4. Bike compatibility match
      if (p.bike_compatibility) {
        for (const b of p.bike_compatibility) {
          if (b.toLowerCase().includes(token)) {
            bestTokenScore = Math.max(bestTokenScore, 10);
            break;
          }
        }
      }
      
      // 5. Typo tolerance (only for tokens >= 5 characters)
      if (bestTokenScore === 0 && token.length >= 5) {
        for (const w of allWords) {
          if (w.length >= 5) {
            const dist = levenshtein(token, w);
            if (dist <= 1) {
              bestTokenScore = Math.max(bestTokenScore, 8);
              break;
            }
          }
        }
      }
      
      if (bestTokenScore > 0) {
        score += bestTokenScore;
        tokensMatched++;
      }
    }
    
    if (tokensMatched === 0) continue;
    
    // Multi-token evaluation
    if (tokens.length > 1) {
      if (tokensMatched === tokens.length) {
        score *= 2.5; // High priority boost when all user terms match
      } else {
        score *= (tokensMatched / tokens.length);
        if (nameMatches === 0) {
          score *= 0.3; // Substantially penalize irrelevant matches that lack name keywords
        }
      }
    }
    
    if (activeBike && window.HRz.DB && window.HRz.DB.checkFitment) {
      if (window.HRz.DB.checkFitment(p.id, activeBike)) {
        score += 10;
      }
    }

    if (score >= 6) {
      scoredProducts.push({ product: p, score: score });
    }
  }

  let result;
  let isFallback = false;
  if (scoredProducts.length > 0) {
    result = scoredProducts
      .sort((a, b) => b.score - a.score)
      .map(item => item.product);
  } else {
    // No scored match at all. This is the normal case for a bike-model
    // query ("Himalayan 450", "Duke 390 Gen-3"): products.json has no bike
    // field and no bike_compatibility on any row, so nothing can score.
    // Never silently return zero: return the closest token matches
    // (smallest edit distance to a name/brand/category/subcategory word,
    // prefix matches counted as distance 0, original order breaks ties)
    // and flag it so callers can show the "no exact fitment data" note.
    // No fitment is invented — these are closest-name matches only.
    isFallback = true;
    const decorated = products.map((p, i) => {
      const words = new Set([
        ...String(p.name || "").toLowerCase().split(/\s+/),
        ...String(p.brand || "").toLowerCase().split(/\s+/),
        ...String(p.category || "").toLowerCase().split(/\s+/),
        ...String(p.subcategory || "").toLowerCase().split(/\s+/)
      ]);
      const cleanWords = [...words].map(w => w.replace(/[^a-z0-9]/g, "")).filter(Boolean);
      let totalDist = 0;
      for (const token of tokens) {
        let best = Infinity;
        for (const w of cleanWords) {
          if (w.startsWith(token) || token.startsWith(w)) { best = 0; break; }
          const d = levenshtein(token, w);
          if (d < best) best = d;
        }
        totalDist += Number.isFinite(best) ? best : token.length;
      }
      return { product: p, totalDist, i };
    });
    decorated.sort((a, b) => (a.totalDist - b.totalDist) || (a.i - b.i));
    result = decorated.slice(0, 20).map(d => d.product);
  }

  // Flags live on the returned array (callers must read them before
  // slice()/filter()/sort(), which create plain arrays). Also recorded
  // on Utils for any caller that only kept the sliced result.
  // noFitmentData is set for known bike-model queries when the catalogue
  // has no fitment data at all — even when incidental token matches
  // (e.g. "450") produced a non-empty scored list. It never claims a
  // product fits the bike; it says the opposite.
  const isBikeQuery = looksLikeBikeModel(tokens);
  let hasFitmentData = true;
  try {
    if (window.HRz && window.HRz.DB && typeof window.HRz.DB.hasFitmentData === "function") {
      hasFitmentData = window.HRz.DB.hasFitmentData();
    }
  } catch (e) { hasFitmentData = true; }
  const noFitmentData = isBikeQuery && !hasFitmentData;
  result.isFallback = isFallback;
  result.searchFallback = isFallback || noFitmentData;
  result.noExactMatch = isFallback || noFitmentData;
  result.fallback = isFallback;
  result.isBikeQuery = isBikeQuery;
  result.noFitmentData = noFitmentData;
  UtilsLastSearch = { query: String(query), tokens, isFallback, isBikeQuery, noFitmentData, count: result.length };
  return result;
}

let UtilsLastSearch = null;
function getLastSmartSearch() { return UtilsLastSearch; }

window.HRz.Utils = { formatCurrency, renderStarRating, showToast, setupModalAccessibility, debounce, escapeHTML, levenshtein, smartSearch, looksLikeBikeModel, sortProducts, isValidSort, isAccessoryProduct, SORT_OPTIONS, SORT_LABELS, normalizeKey, normalizeBrandKey, getLastSmartSearch, get lastSmartSearch() { return UtilsLastSearch; } };
