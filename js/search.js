/* =============================================
   HRz PITSTOP – Search Panel & Autocomplete Module
   Adapted for editorial design search panel
   ============================================= */

window.HRz = window.HRz || {};

class SearchEngine {
  static searchFallback = false;
  static noFitmentData = false;
  static lastSearchQuery = "";

  static init() {
    const input = document.getElementById("globalSearch");
    const popover = document.getElementById("searchAutocomplete");
    const escapeHTML = window.HRz.Utils.escapeHTML;

    if (!input || !popover) return;

    const handleSearch = window.HRz.Utils.debounce(() => {
      const q = input.value.trim().toLowerCase();
      if (q.length < 2) {
        popover.innerHTML = "";
        return;
      }

      const activeBike = window.HRz.Storage.getActiveBike();
      const allProducts = window.HRz.DB.products;
      // NOTE: suggestions are intentionally NOT filtered by the active
      // bike. There is no fitment data for any real product (no
      // bike_compatibility field; compatibility.json references only demo
      // ids), so filtering by bike would empty the suggestions. The old
      // bikeProducts/bikeProductIds computation was dead code and is
      // removed. smartSearch still adds a fitment bonus when a product
      // genuinely matches, via DB.checkFitment.
      const allMatches = window.HRz.Utils.smartSearch(q, allProducts, activeBike);
      // Capture the fallback flag BEFORE slice(5), which strips it.
      // UI reads SearchEngine.searchFallback to show the "no exact
      // fitment data for this bike" note; the matches themselves are
      // closest-name matches, never invented fitment.
      SearchEngine.searchFallback = !!(allMatches && (allMatches.isFallback || allMatches.searchFallback || allMatches.noFitmentData));
      SearchEngine.noFitmentData = !!(allMatches && allMatches.noFitmentData);
      SearchEngine.lastSearchQuery = q;
      const matches = allMatches.slice(0, 5);

      if (matches.length === 0) {
        popover.innerHTML = `<p style="padding:14px;color:#666;">No gear found. Try crash guard or helmet.</p>`;
      } else {
        popover.innerHTML = matches.map(p => `
          <div class="autocomplete-item" data-id="${escapeHTML(p.id)}">
            <img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}" loading="lazy" />
            <div class="info">
              <strong>${escapeHTML(p.name)}</strong>
              <small>${escapeHTML(p.category)} · ${window.HRz.Utils.formatCurrency(p.price)}</small>
            </div>
          </div>
        `).join("");
      }

      popover.querySelectorAll(".autocomplete-item").forEach(item => {
        item.onclick = () => {
          const id = item.dataset.id;
          popover.innerHTML = "";
          input.value = "";
          // Close search panel properly
          if (window.HRz.App) {
            window.HRz.App.closeAllPanels(false, true);
          } else {
            document.getElementById("searchPanel")?.classList.remove("open");
            document.getElementById("overlay")?.classList.remove("open");
          }
          window.location.hash = `product?id=${id}`;
        };
      });
    }, 200);

    input.addEventListener("input", handleSearch);

    // Enter key to go to catalog search
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const q = input.value.trim();
        if (q) {
          popover.innerHTML = "";
          if (window.HRz.App) {
            window.HRz.App.closeAllPanels(false, true);
          } else {
            document.getElementById("searchPanel")?.classList.remove("open");
            document.getElementById("overlay")?.classList.remove("open");
          }
          window.location.hash = `catalog?search=${encodeURIComponent(q)}`;
        }
      }
    });
  }
}

window.HRz.Search = SearchEngine;
