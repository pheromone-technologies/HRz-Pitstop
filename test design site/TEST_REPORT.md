# HRZ Pitstop — Rebuild Test Report

Honest record of what was verified, what failed and was fixed, and what
could NOT be verified without a live browser. This rebuild was coordinated
by a subagent that cannot drive a live browser, so every browser-only check
is listed under "Remains untested" rather than claimed.

## How testing was done

- `node --check` on every JS file (all 15 modules).
- Brace-balance check on every CSS file (all 12 stylesheets).
- `python3 -m http.server` + `curl` for every HTML, CSS, JS, JSON, manifest
  and sitemap asset (36 files, all HTTP 200).
- A Node harness (`/tmp/hrz_test_harness.js`, not shipped) that loads the
  REAL `js/utils.js`, `js/db.js`, `js/catalog.js` and `js/app.js` with DOM
  and localStorage stubs and runs 27 assertions against the real
  `data/products.json` (1,747 products).
- Grep sweeps for misleading wording, bare WhatsApp links, fabricated
  names, and cache-version consistency.

## Passed

- All 15 JS files pass `node --check`; all 12 CSS files have balanced braces.
- All 36 served assets return HTTP 200, including `manifest.json` and
  `sitemap.xml`; `index.html` links the manifest.
- Sorting (Node harness, real data): price-low ascending, price-high
  descending, name A–Z, featured stable order, and sort never mutates the
  master array.
- Category resolution: `Protection` → Crash Protection (151 products),
  `Lights` → Lighting & Electrical, `Luggage`/`Touring` → Luggage & Storage
  (158 products), `Helmets` → Helmets; exact category names pass through.
- Brand normalisation: `MotoTorque` matches `Moto Torque` (169 products).
- Fitment honesty: `getProductsForBike` with a real bike returns an array
  marked `supported: false, reason: "no-fitment-data"`; `hasFitmentData()`
  is false on this data; no fitment mappings were invented.
- Tracking timeline: "Pending WhatsApp Confirmation" maps to the Ordered
  step (0%), "Confirmed" maps to Processing (33%), "Shipped" to Shipped
  (66%), "Delivered" to 100%.
- Search: "crash guard" returns results; "Missing SKU" no longer returns
  the whole catalogue.
- Persistence round-trip (the critical admin fix): a product price edited
  via `DB.updateProduct()` is written to the `hrz_db_products_v31` cache,
  and after wiping in-memory state and re-running `DB.init()` with a
  failing fetch, the edit is restored from cache with the full 1,747-row
  catalogue intact.
- Wording sweeps: no "Secure checkout" / "securely processed via WhatsApp"
  text remains; no `wa.me` link without the store number; no fabricated
  person names (Rahul M. / Ankit S. removed); no "Only N left" urgency text
  anywhere.
- Cache versions: all 27 `?v=` references in `index.html` are consistently
  `v=60`.
- Image safety: the capture-phase global `<img>` error handler in
  `js/image_map.js` swaps ANY failed image (including header/footer brand
  logos) to an inline placeholder exactly once, so the missing `images/`
  and `images_processed/` folders never show broken icons.
- Demo data containment: the demo-product merge into the catalogue is
  commented out in `js/db.js`, so no demo products appear alongside the
  1,747 real products.

## Failed and fixed (found during merge/integration)

1. Catalog "Reset Filters" and drawer "Clear" only cleared advanced
   filters, leaving category, search and sort active. Fixed with a shared
   `Catalog.resetAllFilters()` that also clears category, subcategory,
   search and sort and strips catalog URL params so a reload cannot
   restore the cleared filters.
2. Order timeline stuck at 0% for the admin statuses "Pending WhatsApp
   Confirmation" and "Confirmed" (they mapped to no timeline class).
   Fixed in `App.getOrderStatusClass`: Pending → Ordered step (0%),
   Confirmed → Processing (33%).
3. Product-page installation gallery carried fabricated captions
   ("Installed by Rahul M. · Bengaluru", "Installed by Ankit S. · Pune")
   and a "Verified Installation Photos" heading for every product. Fixed
   with neutral "Illustrative installation photo / Example fitment photo"
   captions and an "Installation Gallery" heading.
4. Blocked-popup WhatsApp path showed a link that did not clear the bag
   or record the order. Fixed: the manual button now opens WhatsApp AND
   runs the same finalise step (clear bag, save order, show success view)
   as the popup path.

## Remains untested (needs a live-browser pass — NOT claimed as done)

- Real rendering at 375px viewport: no overflow, dock behaviour, drawer
  layering over checkout.
- Tap interactions: bottom dock navigation, wishlist badge on real tap,
  add-to-bag, BUY NOW navigation in a real tab.
- Cart surviving a real page reload, and an admin edit surviving a real
  reload on the live storefront (the cache round-trip was verified in
  Node, not in a browser tab).
- Admin PIN set/unlock flow in a real tab (logic verified in Node by the
  admin worker's harness, not in a browser).
- The blocked-popup WhatsApp branch in a real browser (popup blockers
  cannot be simulated in Node).
- The `#catalog?brand=MotoTorque` and `?sort=` URL behaviours in a real
  browser address bar (logic verified in Node).
- Any visual check of the liquid-glass styling, spacing, or typography
  (no screenshots were taken).

## Known limitations (by design, not bugs)

- Admin PIN is a client-side deterrent (SHA-256 hash in localStorage,
  sessionStorage unlock), not real security — stated on the gate screen.
- Rating sort is a stable no-op because every product in this data is
  rated exactly 4.8; no fake differentiation was added.
- Product pages show "No verified rider reviews yet" because
  `reviews.json` holds only 3 reviews for demo ids no real product
  matches; the 4.8 stars and review counts are no longer displayed.
- No service worker: deliberately omitted to avoid stale-cache risk.
- No payment gateway: settled client requirement; checkout is
  WhatsApp-only with the store number 917019348327.
