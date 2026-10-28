# HRZ Pitstop — Rebuild Change Log

Every change made during the rebuild, file by file. The site stays vanilla
JS with no build step and deploys as static files on Vercel.

## Logic fixes (catalogue, categories, sorting, search, persistence)

### js/db.js
- `_persist()` now actually writes every collection, including the
  `hrz_db_products_v31` products cache (previously products were skipped,
  so every reload re-fetched JSON and wiped admin edits and checkout
  orders). Each key is written independently, so a quota failure on the
  ~1.5 MB products write no longer loses orders/reviews.
- `init()` uses the cache when present (with a `v31` version guard) and
  falls back to fetching JSON on missing/corrupt/mismatched cache — and
  to any parseable cache if the fetch itself fails.
- Fitment honesty: new `DB.hasFitmentData()` (false on current data —
  no product carries `bike_compatibility`, and `compatibility.json`
  references only demo ids), `DB.getFitmentStatus()` returning
  `{supported: false, reason: "no-fitment-data"}`, and
  `DB.getProductsForBike()` returning an array carrying `supported` /
  `reason` properties instead of a bare empty list. No fitment mappings
  were invented.
- `checkFitment()` intentionally still returns the fitment object or
  `null`: returning a truthy no-data object there would wrongly mark
  every product compatible for existing callers.

### js/catalog.js
- New `Catalog.resolveCategory()`: exact real category wins, then the
  alias map Protection → Crash Protection, Lights → Lighting &
  Electrical, Luggage/Touring → Luggage & Storage, Helmets → Helmets,
  then a department fallback. Category pages and filters no longer land
  on "No Parts Found" for categories that have products.
- New reusable `Catalog.sortProducts(products, sortBy)` (featured /
  price-low / price-high / rating / name): stable, never mutates the
  master array, non-numeric prices sort last, rating is a documented
  stable no-op because all ratings are 4.8. Applied after
  filtering/search in `render()`. Drawer gains a Name A–Z option.
- Sort persists in the URL via `syncSortToUrl()` (category-pill clicks
  preserve it; `featured` removes the param), so reload, back and shared
  links keep the sort.
- `?category=` / `?brand=` URL-param support in `render()`.
- Brand filtering normalised (spaces/case stripped), so
  `?brand=MotoTorque` matches "Moto Torque".
- Added the missing `Catalog.getDepartment()` — home filter buttons
  previously threw on it and did nothing.
- Merge fix: new `Catalog.resetAllFilters()` — both "Reset Filters" and
  drawer "Clear" now clear category, subcategory, search, sort AND
  advanced filters, and strip catalog URL params so a reload cannot
  restore cleared filters.

### js/utils.js
- Single sort implementation `Utils.sortProducts()` (which
  `Catalog.sortProducts` delegates to), plus `normalizeKey` /
  `normalizeBrandKey`.
- `smartSearch` fixes: concatenated brand/category matching
  ("MotoTorque" → "Moto Torque"), the "Missing SKU" placeholder no longer
  matches the whole catalogue, and a known-bike-model detector
  (`looksLikeBikeModel`, checked against `bikes.json`).

### js/search.js
- Suggestions keep slice-5 and Enter → `#catalog?search=` behaviour.
- Removed the dead `bikeProducts` / `bikeProductIds` computation
  (filtering suggestions by bike would empty them, since no fitment
  data exists); fallback/no-fitment flags captured into
  `SearchEngine.searchFallback` / `SearchEngine.noFitmentData` for the UI.

### js/menu.js
- Brand list corrected to canonical exact values from the data (Moto
  Torque, AXOR, Legundary, Scala Gears, STUDDS, VEGA, RAIDA); brand
  links emit `#catalog?brand=<canonical>`; category "view all" and
  section links emit canonical `#catalog?category=` params.
- The "100%" menu item is not a brand value in the data (it appears in
  product names only), so it stays a keyword `?search=` link, which
  returns matches, rather than an empty brand filter.
- Protective Armour / Riding Suits / Touring Accessories cards kept on
  department routes — they have no single exact category, so converting
  them would narrow or mislabel them.

### js/seo.js
- New `updateTitleAndDescription()` reading live hash params, so titles
  and descriptions reflect category / subcategory / search / brand /
  sort (e.g. "Crash Protection (Price: Low to High) | HRz Pitstop").
- Home/unknown views restore the original title/description; catalog
  JSON-LD gains a breadcrumb for the active category/search/brand.

## Commerce fixes (cart, checkout, product, garage, images)

### js/cart.js
- New single `Cart.buyNow()` path: adds exactly once, never opens the
  drawer, closes any open drawer, navigates to `#checkout` (no 100 ms
  timer). Product-page BUY NOW uses it; a `hrz:buy-now` event exists for
  any future quick-view.
- Persistent guest/login-prompt gate: the flag is saved before the
  popup shows, so dismissing it and reloading never re-prompts, and the
  first post-reload "+ Bag" is no longer discarded.
- `addItem()` dedupes by base id + variant colour (colour preserved on
  the stored row so dedupe survives reload); `updateCartBadge()` is
  guarded against missing elements; drawer checkout button honours the
  durable guest choice.

### js/storage.js
- Added `loginPrompted: false` to persisted app state plus
  `hasLoginPrompted()` / `setLoginPrompted()`; existing `getCart` /
  `setCart` and the `hrz_pitstop_app_state_v10` key are unchanged.

### js/checkout.js
- Single top constant `WHATSAPP_NUMBER = "917019348327"` (India code 91 +
  7019348327, taken from the live site's floating WhatsApp button) used
  in every `wa.me/<number>?text=…` link — previously the link had NO
  number at all.
- "Payment Method" → "How you'll pay" with the note "No online payment
  here — you confirm and pay with us on WhatsApp"; submit button →
  "Order on WhatsApp (₹X)"; all "securely processed via WhatsApp"
  wording removed.
- Cart cleared and order saved ONLY when a handoff actually happens:
  on a blocked popup the bag is kept intact and a manual button is
  shown. Merge fix: tapping that manual button now also clears the bag
  and records the order, since tapping it IS the handoff.
- Order-summary header and bike banner use total units, not
  distinct-line count (fixed the Qty label inconsistency).

### js/product.js
- Rating block no longer renders the uniform 4.8 stars, reviewCount or
  ridersInstalled (all 1,747 products are 4.8 with reviewCount 8/12 and
  ridersInstalled 32/45; `reviews.json` holds only 3 reviews for demo
  ids no real product matches). Now shows "No verified rider reviews
  yet" (or the real published-review count when one exists).
- Related products use a fallback chain (bike-filtered same-category →
  same-brand → rest → all same-category → same-brand → all), never
  empty when same-category products exist.
- Fitment banner handles both `null` and `{supported: false}` shapes and
  says "Fitment data not available for this bike yet" instead of
  "Universal" when a bike is chosen with no data.
- Merge fix: installation gallery captions neutralised — the fabricated
  "Installed by Rahul M. · Bengaluru" / "Installed by Ankit S. · Pune"
  attributions and the "Verified Installation Photos" heading are
  replaced with "Illustrative installation photo / Example fitment
  photo" and an "Installation Gallery" heading.
- Product-page BUY NOW calls shared `Cart.buyNow()`; every
  product/viewer/thumbnail/carousel/install image uses the data-URI
  placeholder fallback.
- No "Only N left" urgency text was added: no product carries a real
  quantity field (stockQty/quantity on 0 of 1,747 rows).

### js/garage.js
- When a bike is selected and the bike-filtered list is empty (no
  fitment data), shows the first 10 catalogue products with the note
  "Fitment data not available for this bike yet — showing all gear"
  instead of an empty grid.
- "Guaranteed fitment parts only" / "demo catalog" copy removed.

### js/image_map.js
- Defines `window.HRzPlaceholderImage` (inline data-URI SVG: grey gear
  silhouette, "HRz Pitstop" text — no external file, no hotlinking) and
  `HRzImageMap.PLACEHOLDER`.
- Original bike-image map values kept so real images work if restored.
- Capture-phase global `<img>` error handler swaps any failed image on
  the page to the placeholder exactly once, so the missing `images/` and
  `images_processed/` folders never show broken icons.

## Admin panel

### js/admin.js
- Gate enforcement in `AdminCMS.render()`: requires `Auth.isLoggedIn()`
  AND `Auth.isAdminUnlocked()` before rendering any admin UI; failing
  either renders only a gate screen with no data. "Continue as Guest"
  is explicitly rejected for admin.
- PIN: first run, a signed-in admin sets a PIN (4–8 digits, confirmed);
  no default PIN exists anywhere. Later visits require the PIN, stored
  only as a SHA-256 hash (`hrz_admin_pin_hash_v1` in localStorage;
  weak-hash fallback only if Web Crypto is unavailable). Unlock is a
  sessionStorage flag (closing the tab re-locks); topbar has a "Lock
  admin" button; signing out clears unlock. Honest limitation stated in
  code comments and on the gate screen: client-side lock only, a
  deterrent, not real security.
- Catalogue tab: debounced search (250 ms), category pill filter, In
  stock / Out of stock filter, "Showing X of Y products" count; per-row
  Quick edit (price input + In Stock/Out of Stock select + Save/Cancel)
  with validation (price non-negative; empty name rejected) calling
  `DB.updateProduct()` → `DB._persist()`, with inline "✓ Saved" badge +
  toast; full Edit modal with the same validation.
- Reset-to-original-catalogue button (confirms, re-fetches
  `data/products.json`, replaces `DB.products`, removes the
  `hrz_db_products_v31` cache key, reloads; honestly warns saved
  order/review changes are also lost on next load).
- Add-product form no longer generates HRZ-xxxx SKUs (blank stays blank)
  and no longer fabricates `originalPrice = price + 500`; invented "NEW
  ARRIVAL" badge/highlights defaults removed.
- Orders tab: search by order ID / tracking ID; status select with the
  flow Pending WhatsApp Confirmation → Confirmed → Shipped → Delivered
  (plus Cancelled and legacy values) via `DB.updateOrderStatus()` →
  `DB._persist()`; fixed the display bug where "Pending WhatsApp
  Confirmation" showed as "Order Placed" (current status is always
  included as the selected option, including legacy "In Transit").
  Tracking page reads the same `DB.getOrders()`, so it shows updated
  status text.

### js/auth.js / css/auth.css
- Sign-in reuses `Auth.showLoginPopup`; admin gate integrates with the
  existing auth state. Popup layouts are `min(460px, 100%)` / 92vw with
  stacked small-screen layouts.

### css/admin.css
- ≥44px tab buttons, actions, selects and pills; tables scroll
  horizontally inside a wrapper instead of overflowing at 375px.

## UI overhaul (mobile-first, premium)

### index.html
- Bottom dock: Home / Shop / Search / Wishlist / Bag (Garage removed
  from the dock, still reachable via `#garage`).
- Footer Shop links use real category hashes (`#catalog?category=Crash
  Protection`, Helmets, Lighting & Electrical, Luggage & Storage).
- Cart drawer button "Secure checkout" → "Order on WhatsApp".
- Floating WhatsApp button → `https://wa.me/917019348327`.
- `<link rel="manifest">` and a data-URI `og:image` added (no file
  references); all `?v=49` cache strings bumped to `?v=60` (27 refs).

### css/base.css, layout.css, header.css, menu.css, product.css, garage.css, cart.css, footer.css, orders.css, responsive.css
- iOS-style liquid-glass treatment: translucent blurred surfaces
  (`backdrop-filter` blur/saturate), soft specular highlights, smooth
  spring-like transitions (`cubic-bezier(0.34, 1.3, 0.64, 1)`).
- 44px+ touch targets, consistent spacing and typography, 375px
  guardrails, `prefers-reduced-motion` respected.

### js/app.js
- Dock active state maps views to the nearest dock item; wishlist badge
  syncs on route change, on `Storage.toggleWishlist`, and on storage
  events.
- Home sort now uses the shared sorter when present (with a local
  comparator fallback); the home filter crash is guarded (falls back to
  `Catalog.isProductInDepartment()`, then plain category match).
- Merge fix: tracking timeline now handles the admin statuses —
  "Pending WhatsApp Confirmation" → Ordered step, "Confirmed" →
  Processing (33%).

### manifest.json (new), sitemap.xml (new)
- PWA manifest: name "HRz Pitstop", short name "HRz", theme/background
  `#0d0e10`, icon as inline SVG data URI only (no image files).
- Sitemap: hash views home, catalog, wishlist, tracking, reviews, help,
  about.

## Deliberately left out, and why

- **No payment gateway.** Settled client requirement: customers order
  via WhatsApp to avoid the ~2% fee. All checkout wording is honest
  about this.
- **No service worker.** Stale-cache risk on a static site whose data
  file changes; installability is provided by the manifest alone.
- **No invented SKUs, categories, prices, reviews, or fitment data.**
  Blank fields stay blank; the 1,747-row catalogue is untouched in
  content (only its loading, filtering, sorting and persistence changed).
- **No live-browser verification.** The coordinating subagent cannot
  drive a live browser; see TEST_REPORT.md for the exact untested list.
- **Home bestsellers grid still shows the existing 8-item set**, not
  expanded to the full catalogue (kept the existing home design).
- **Demo fallback in `js/db.js` left as-is**: demo products are only
  used if `data/products.json` fails to load entirely; the merge of demo
  products into the live catalogue is commented out and stays that way.
- **The reference spreadsheet `Verified_Products_FINAL-1.xlsx` is NOT
  included in the deliverable zip**: it is inventory reference data,
  not site source, and the user already has it.
- **No "Only N left" stock urgency, no differentiated ratings, no
  fake reviews**: the underlying data does not support them.

## v2 fixes (2026-10-27, after Sunil's feedback on the v1 rebuild)
- Fog Lights showing electronics: root cause was `isProductInDepartment` lumping
  the whole Electronics category (59 products: intercoms, GPS mounts) into the
  Lighting & Electrical department. Fixed three ways: Electronics is now its own
  department (own pill + `#electronics` route); Lighting & Electrical matches
  only `Lighting & Electrical` (140 products, was 199); the home "Fog Lights"
  filter now matches the Fog & Aux Lights subcategory only (37 products, zero
  electronics). `normalizeCategory("electronics")` no longer maps to Lighting.
- "All Shop All" glitch: the Shop All subcategory pill label is now "Shop All".
- Category pages: when a category is open, the global category pill row is
  hidden; the page shows only that category's subcategories, with a back bar
  ("← All Categories" + product count) and breadcrumb Home / Shop All / Category.
- Bottom dock restyled to a floating capsule (Apple/WhatsApp style): fully
  rounded pill, centred, floating above the bottom edge, liquid-glass blur,
  soft shadow; active item gets a subtle pill background. Body bottom padding
  raised so content clears the floating capsule.
- Verified with a Node harness against the real 1,747-row catalogue: 26/26
  checks pass (filter separation, department counts 140/59, fog-only filter,
  Shop All vs category-page rendered HTML).

## v3 fix (2026-10-27, Sunil: menu clicks bypass the v2 category-page fix)
- Root cause: the "Motorcycle Accessories & Parts" mega-menu (and Shop by Bike /
  Brands menus) link via `#catalog?search=<term>`, which carries NO category, so
  the catalog route renders category "All" and the v2 dedicated-page fix never
  triggered — menu clicks landed on the full Shop All view with both pill rows,
  and the subcategory row showed all 1,747 products' subcategories.
- Search mode is now a dedicated page too: the global category row is hidden,
  the subcategory row reflects ONLY the search results, the header reads
  RESULTS FOR "<term>" with a back-to-Shop-All bar and result count, and the
  breadcrumb reads Home / Shop All / Search: "<term>". First subcategory pill
  reads "All Results". This covers every ?search= menu link at once.
- Verified with the render harness against the real catalogue: 34/34 checks
  pass (26 v2 checks + 8 search-mode checks, incl. a simulated
  #catalog?search=CRASH GUARD menu click).

## v4 (2026-10-27, Sunil: missing basics + incomplete subcategories + completion check)
- Card quantity stepper: + Bag now turns into a - qty + stepper the moment an
  item is in the bag, on every card surface (catalog, home, wishlist, related).
  Minus at 1 removes the item and the button reverts to + Bag. Previously the
  button stayed "+ Bag" no matter how many units were added.
- Product page: quantity selector before Add to Bag; Add to Bag, Buy Now and
  the new sticky bar all buy the chosen quantity (Cart.addItem/buyNow now
  accept a quantity). Related-product card buttons were previously dead
  (product page never bound them) — now bound.
- Discount % OFF badge on cards and product page whenever a genuine
  strikethrough price exists (computed from real prices, never invented).
- Drawer subcategory fix: the filter drawer's subtype list was name-keyword
  guesses for only 4 hardcoded categories (Helmet Accessories, Visors &
  Spoilers, Headlight Grills, Touring Bags, Luggage Racks & Stays and all
  Lighting/Electronics/Performance/Maintenance subtypes never appeared).
  It now lists ALL real subcategories of the current category/search scope
  for every category, and the filter matches real subcategories.
- Recently Viewed on home no longer falls back to bestsellers when empty
  (that mislabelled them as viewed); the section now appears only for
  genuine viewing history.
- Product page: Share button (system share sheet, clipboard fallback),
  honest delivery estimate (dispatched within 24h, free above Rs 2,999,
  Rs 199 below — per the store's own FAQ, no invented pincode dates),
  sticky mobile buy bar above the capsule dock.
- Cart drawer: Clear bag + Continue shopping actions.
- Verified: 19/19 v4 checks + 10/10 v2/v3 regression checks against the
  real 1,747-row catalogue.

## v5 (2026-10-27, Sunil: stepper glitches, oversized button, stale Add to Bag)
- Root cause of "clicking the product adds item to cart": on mobile the
  product page's buy row was `position: fixed` across the very bottom of the
  screen, permanently covering page content and intercepting taps meant for
  products below it (and sitting above the dock). It is back in normal flow.
  The sticky bar is now scroll-aware: hidden until the main buy row scrolls
  off-screen, then appears; its listener removes itself when the view goes.
- "Add to cart again" after adding: the product page never reflected bag
  state. Now Add to Bag becomes a - qty + stepper (main row AND sticky bar)
  the moment the current variant is in the bag, and reverts when it leaves;
  variant switches re-sync, since each variant has its own bag entry.
- Oversized card button: card + Bag is now a compact 36px pill and the card
  stepper matches, leaving most of the card for opening the product.
- Glass pill styling on the product page: the purchase row is now a
  liquid-glass pill bar (blur, translucent, rounded) matching the home dock;
  the qty selector and share button get the same glass treatment.
- Verified: 11/11 v5 checks + 19/19 v4 checks + 10/10 v2/v3 regression checks.

## v6 (2026-10-27, Sunil: think first — one buy control, dock-style capsule)
- Thought through before changing: the product page had THREE quantity
  controls (separate quantity selector + stepper + buy capsule). Now there
  is exactly one buy control per screen, and the stepper IS the quantity
  control — the separate quantity selector is gone entirely.
- Mobile: a single PINNED bottom capsule in the home dock's exact style
  (floating centred glass pill: rgba(16,17,20,0.72), blur 22px saturate
  180%, 999px radius, same shadow, sitting above the dock) holding
  [Add to Bag <-> - qty + stepper] + [Buy Now]. The in-flow purchase row
  is hidden on mobile so the two never duplicate; a clearance spacer keeps
  the last content from hiding under capsule + dock.
- Desktop keeps the in-flow purchase row as its buy control; the capsule
  is mobile-only, as the dock is.
- Buy Now buys the stepper quantity when the item is in the bag, else 1.
  First add puts exactly 1 in the bag; the stepper adjusts from there.
- Share moved next to the product title (small glass icon button) so it
  survives the quantity-row removal. Scroll-gated sticky logic removed:
  pinned means pinned.
- Verified: 13/13 v6 checks (incl. a real product-page render) + 19/19 v4
  checks (2 updated to the new intended behaviour) + 10/10 v2/v3 checks.

## v7 (2026-10-27, Sunil: screenshot — capsule stepper looked wrong)
- The capsule was right; the stepper inside it was not: it rendered as a
  second grey pill nested inside the glass capsule, with big solid red
  circles fighting BUY NOW for attention. The stepper container inside
  the capsule is now transparent with no border, and its - / + buttons
  are quiet ghost circles (white 12%), so BUY NOW is the single red
  accent and the capsule reads as one clean control, like the dock.
  Card steppers elsewhere keep their solid red buttons — only the
  capsule stepper changed.
- Verified: 9/9 v7 checks (incl. a real product-page render). Catalog and
  cart code untouched by this change.

## v8 (2026-10-27, Sunil: no dock on product pages; card qty ≠ page qty)
- Product pages own the bottom: the router now adds an is-product-page
  body class on the product route, the dock is hidden there, and the buy
  capsule moves down into the dock's exact spot (bottom 12px) instead of
  stacking above it. Two stacked capsules eating the screen is gone;
  the now-redundant capsule clearance spacer is removed (the 96px body
  padding already clears the capsule).
- Quantity mismatch root cause: the card adds the base id, but the
  product page suffixed EVERY variant — including the default — so a
  card-added quantity was invisible on the page. The base id IS the
  default variant now; only non-default variants get a suffixed id.
  Cards show the family total (base + variant entries) and their
  steppers resolve to the real entry (base first, else a variant), so
  card and page can no longer disagree in either direction. The drawer
  still lists each variant entry separately, as it should.
- Verified: 15/15 v8 checks (incl. the exact reported scenario, variant-
  only bags, mixed bags, and the dash guard against prefix leaks).
