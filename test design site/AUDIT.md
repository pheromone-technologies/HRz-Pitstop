# HRz Pitstop — Static Storefront Audit

**Scope & method:** read-only static review of this zip only. No site file was edited.
Every JS module in `js/` (15 files, 7,534 lines), `index.html` (268 lines) and the
CSS file list were read; `data/*.json` were counted programmatically. Nothing was
run in a live browser, so behaviours that only appear at runtime (exact rendered
pixels, network timing, storage in a particular browser profile) are flagged as
such rather than asserted. Line numbers are from the files as received.

**Headline numbers (this zip, not any other deliverable):**

| Item | Value |
|---|---|
| Products in `data/products.json` | **1,747** (top-level JSON array; 0 duplicate `id`s, 10 duplicate `name`s) |
| Real categories in `products.json` | 28 (see §2) |
| Departments (pills) in `catalog.js` | 8 (see §2) |
| Bikes in `data/bikes.json` | 53; compatibility rows: 21; reviews: 3; orders: 2; bundles: 2 |
| Products with a real SKU (not `"Missing SKU"`) | 283 of 1,747 (1,464 = `"Missing SKU"`) |
| Products with empty `subcategory` | 183 |
| Products with `variants` | 33; with `bike_compatibility` | 0; with `description` / `sizes` / `badge` / `authenticity` | 0 |
| Every product's `rating` | 4.8 (all 1,747); `reviewCount` 8 (1,714) or 12 (33); `inStock` always `true` |
| Image folders `images/` and `images_processed/` | **Absent from this zip** (README.md still lists them) |

---

## 1. How products load from `data/products.json`

**Module:** `js/db.js` — `DBService.init()` (lines 283–362), called first from
`js/app.js` `App.init()` (line 9: `await window.HRz.DB.init()`). Load order in
`index.html` lines 41–56 is `storage.js, auth.js, image_map.js, db.js, utils.js,
seo.js, garage.js, catalog.js, product.js, cart.js, checkout.js, search.js,
admin.js, menu.js, app.js` (all `?v=49`, plus PapaParse from CDN for CSV import).
The app **must be served over HTTP** — `db.js` itself warns that `file://` fails
(see `loadError` handling, lines ~321–340, and the toast
`"Failed to load product data! … you must use a local server instead."`).

**Flow:**

1. `DBService.init()` first calls `Storage.cleanupLegacyKeys([...CACHE_KEYS])`
   (`js/storage.js` lines 33–51), which deletes any `hrz_*` localStorage key not in
   the protected set.
2. It reads six localStorage cache keys (`CACHE_KEYS`, `db.js` lines 8–15,
   `hrz_db_*_v31`). **Only if `cachedBikes && cachedProducts && cachedComp` are
   all present** does it use the cache (lines ~296–306).
3. Otherwise it `fetch`es all six JSON files in parallel (lines ~308–321):
   `data/bikes.json`, `data/products.json`, `data/compatibility.json`,
   `data/reviews.json`, `data/orders.json`, `data/bundles.json`. Any fetch failure
   zeroes **all** collections and sets `loadError`; `app.js`
   `syncDataLoadBanner()` (lines 175–210) then shows a red banner. There is no
   partial fallback and no retry.
4. It then calls `_persist()` (lines 364–376) — see the critical flaw in §11, C2.

**The product object** (as stored in this zip) has exactly these fields —
`id, name, brand, category, subcategory, price, originalPrice, image, gallery,
sku, rating, reviewCount, ridersInstalled, inStock, highlights`, plus `variants`
on 33 rows. There is **no** `description`, `sizes`, `badge`, `authenticity`,
`warranty`, `bike_compatibility`, `fitmentCategories`, `stockQty` or `isVisible`
field on any real row (the product-page code reads several of these anyway, so
they silently fall back — see §9). Sample (first row, verbatim):

```json
{
  "id": "hrz-3000-4t-plus-15w50-2-5ltr-0002",
  "name": "3000 4T PLUS 15W50 2.5LTR",
  "brand": "Motul",
  "category": "Engine Oils & Lubricants",
  "subcategory": "",
  "price": 1299.0,
  "originalPrice": 1299.0,
  "image": "images_processed/catalog/motul/3000_4t_plus_15w50_2_5ltr.webp",
  "gallery": ["images_processed/catalog/motul/3000_4t_plus_15w50_2_5ltr.webp"],
  "sku": "Missing SKU",
  "rating": 4.8,
  "reviewCount": 8,
  "ridersInstalled": 32,
  "inStock": true,
  "highlights": [
    "Official genuine Motul motorcycle component",
    "Tested and verified on high-performance builds",
    "Backed by HRz Pitstop Fitment Guarantee"
  ]
}
```

Accessors: `DB.getProducts()` (line 379), `getProductById(id)` — a linear
`.find()` (line 380), `getCategories()` — distinct `p.category` values, sorted
(lines 386–390). Note the dead demo layer still in the file: `DEFAULT_PRODUCTS`
(6 demo products with short categories `Helmets / Protection / Lights / Luggage /
Touring`, lines ~70–180), `DEFAULT_BIKES` (18), `DEFAULT_COMPATIBILITY`,
`DEFAULT_REVIEWS`, `DEFAULT_ORDERS`, `DEFAULT_BUNDLES`, and `DEMO_PRODUCT_GROUPS`
plus `buildDemoProducts()` which now returns `[]` (line 269) and whose merge line
is commented out (line ~352). The demo ids (`axor-helmet`, `crash-guard-steelmoto`,
`fog-lights-led`, `saddlebags-touring`, `brake-pads-ceramic`,
`windshield-adventure`) do **not** exist in `products.json`, yet
`compatibility.json`, `reviews.json`, `orders.json` and `bundles.json` all still
reference them — see §9/§11.

---

## 2. Categories: how they link to products, and exactly why links land empty

### 2.1 The three different category vocabularies in the codebase

| Layer | Vocabulary | Where |
|---|---|---|
| Real data | 28 categories, e.g. `Helmets` (383), `Riding Jackets & Apparel` (195), `Luggage & Storage` (158), `Crash Protection` (151), `Lighting & Electrical` (140), `Body Parts & Panels` (104), `Gloves` (102), `Electronics` (59), `Mirrors & Handlebar Accessories` (59), `Braking Components` (55), `Drive & Transmission` (51), `Maintenance & Cleaning` (50), `Engine Oils & Lubricants` (38), `Unclassified — Needs Verification` (39), `Covers` (13), `Locks & Security` (2), `Merchandise & Decals` (3), `Other — Non-Motorcycle Items` (1) | `data/products.json`; `db.js getCategories()` |
| Department pills | Only **8** departments | `catalog.js` `DEPARTMENTS` (lines 32–41): `All / Helmets / Riding Gear / Crash Protection / Luggage & Touring / Lighting & Electrical / Performance / Maintenance & Cleaning`, with slugs `catalog / helmets / riding-gears / protection / luggage / lights / performance / maintenance` |
| Old demo vocabulary | `Protection, Lights, Luggage, Touring` (not real categories) | `db.js DEFAULT_PRODUCTS`, `app.js` home filters, `menu.js` copy |

### 2.2 How filtering works (`catalog.js`)

- `normalizeCategory(cat)` (lines 43–55) collapses a label to a department by
  substring matching, in this order: `helmets|helmet → Helmets`;
  `gear|jacket|apparel|riding → Riding Gear`; `protect|crash → Crash Protection`;
  `luggage|touring|storage → Luggage & Touring`; `light|electron → Lighting &
  Electrical`; `perform|part|exhaust → Performance`; `maint|oil|clean →
  Maintenance & Cleaning`; otherwise the input is returned **unchanged**.
- `isProductInDepartment(p, category)` (lines 56–83) then tests the product's
  real category against the normalised department with hard-coded lists, e.g.
  Riding Gear = `Riding Jackets & Apparel, Gloves, Riding Pants, Boots & Footwear,
  Protective Gear`; Performance = `Performance Parts, Exhaust System, Drive &
  Transmission, Braking Components, Suspension Components, Engine Components,
  Cables & Controls, Body Parts & Panels, Mirrors & Handlebar Accessories, Tyres
  & Wheels`; Maintenance & Cleaning = `Engine Oils & Lubricants, Maintenance &
  Cleaning, Tools & Workshop Equipment`. Anything not matched falls through to
  `pCat.includes(norm.toLowerCase())`.
- `CatalogView.render()` (lines 120+) pipeline, in order: copy all products →
  `smartSearch` if `searchQuery` → department filter → subcategory filter →
  brand / colour / subtype / price filters → sort (§3) → render. Pill counts are
  computed from `allBaseProducts` filtered **only by department** — they ignore
  search text, subcategory, brand, colour and price, so the count on a pill can
  disagree with the grid shown.
- `getProductSubcategory(p)` (lines 85–107): real `subcategory` if present, else
  category-based fallbacks (`Gloves → Riding Gloves`, etc.) and name-based
  fallbacks (`crash guard → Crash Guards`, `slider → Frame Sliders`, …), else the
  raw category. `matchesSubcategory()` (lines 108–118) accepts an exact derived
  match, an exact raw-`subcategory` match, or a product **name containing** the
  target string.
- Route → department mapping is in `app.js handleRoute()` (lines 212–348):
  `#helmets → category "Helmets"`, `#riding-gears/#riding-gear/#jackets →
  "Riding Gears"`, `#protection/#crash-guards → "Protection"`,
  `#luggage → "Luggage"`, `#lights/#lighting → "Lights"`,
  `#performance → "Performance"`, `#maintenance → "Maintenance"`,
  `#catalog?category=…&subcategory=…&search=…` passed through verbatim. Category
  pills (`catalog.js bindSliderEvents`, lines 504+) set `activeCategory` to the
  pill's `data-cat-id` and navigate to its `data-slug`; subcategory pills use
  `history.replaceState` (not a hash change) and re-render in place.

### 2.3 The exact empty-result mechanisms (verified against the data)

**A. Shop-by-Bike / brand / accessory menu links are searches, not filters —
and the thing they search for does not exist in the data.**
`menu.js` `menuData.shopByBike` (~60 models), the accessory lists and the brand
list overwhelmingly link to `#catalog?search=<label>` (desktop mega-nav lines
~137–482, mobile drawer lines ~483–793, `navigateToSearch()` line 951), and
`app.js renderModelsView()` (lines 1369–1402) does the same for every model
click. But `smartSearch` (`utils.js` lines 137–260) only scores a product on its
**name, brand, category, subcategory, SKU and `bike_compatibility` words**.
`products.json` has **no bike field at all and `bike_compatibility` on 0 of
1,747 rows**, so a bike-model search can only score incidental word matches
(e.g. a capacity number inside a product name) and multi-token partial matches
are then penalised (`score *= tokensMatched/tokens.length`, and `× 0.3` if no
name word matched). The result for a model link is therefore empty or irrelevant
— the "NO PARTS FOUND" card (`catalog.js` lines ~358–365). The same applies to
menu brand labels that do not match a real `brand` value word-for-word
(`MotoTorque` in the menu vs `Moto Torque` in the data; `Legundary Customs`,
`Royal Enfield` as a *brand* search, etc.) and to accessory labels such as
`Lock system`.

**B. The bike-fitment filter itself returns (almost) nothing.**
`db.js getProductsForBike(activeBike)` (lines 476–480) keeps only products where
`checkFitment()` (lines 392–474) is non-null. Step 1 needs
`product.bike_compatibility` (absent on all rows); step 2 needs a
`compatibility.json` row for that product id — but all 21 rows reference the
six demo ids, none of which are in `products.json`; step 4 needs
`product.fitmentCategories` (absent on all rows). Step 3 only blocks the
demo categories `Protection / Lights / Accessories`, which no real category
equals. **So with any bike selected, `getProductsForBike()` is effectively
empty.** That empties: home bestsellers after a bike is chosen, garage
recommendations (`garage.js` line 246), product-page "Related Products"
(`product.js` line 283), and the home filter path (`app.js` lines 588–592).
Critically, `CatalogView.render()` **never calls `getProductsForBike()` at all**
— it starts from `DB.products` — so the catalogue ignores the selected bike
while every other surface honours it. The site therefore contradicts itself:
catalogue shows everything, home/garage/related show nothing, for the same bike.

**C. Five real categories have no department pill and no route.**
`Covers` (13), `Unclassified — Needs Verification` (39), `Other —
Non-Motorcycle Items` (1), `Locks & Security` (2) and `Merchandise & Decals`
(3) — 58 products — match no `DEPARTMENTS` entry. They are reachable only via
"Shop All" or via the filter drawer's raw-category radio list
(`catalog.js` line ~398, which uses `DB.getCategories()`). Their pill row shows
no active pill when reached via `?category=…`, because `normalizeCategory`
returns them unchanged and no pill's normalised id equals them. (They are not
themselves empty — the fallback `pCat.includes(norm)` in
`isProductInDepartment` does match them — they are simply unfindable.)

**D. Colour filtering empties 98% of the catalogue.**
`catalog.js` colour filter requires `p.variants` and a variant colour match;
only 33 of 1,747 products have `variants`. Picking any colour therefore drops
~1,714 products, including every product the colour was supposedly filtering.

**E. "Reset Filters" does not reset the most common cause of emptiness.**
The empty-state button (`catalog.js` lines 363 and 478–486) calls
`resetAdvancedFilters()` (brands/colours/subtypes/prices) and sets subcategory
to `All`, but **does not clear `searchQuery` or `activeCategory`**. If the page
is empty because of a search term (mechanism A — the commonest case), Reset
re-renders the same empty result.

**F. Subcategory menu cards mostly work — but only by accident of the data.**
Because most rows *do* carry a real `subcategory`, the menu-card links
(`#helmets?subcategory=Full Face`, `#riding-gears?subcategory=Jackets`,
`#luggage?subcategory=Touring Bags`, … in `menu.js` lines ~100–129) do match
via `getProductSubcategory`/`matchesSubcategory`. They break only where the
target is a derived label with no matching raw subcategory and no name hit
(e.g. `#riding-gears?subcategory=Apparel` relies on a name containing
"apparel"), and where the department filter runs first: a subcategory that
exists under a *different* department than the route's department can never
appear. Note also that subcategory pills use `replaceState`, so the search
term (if any) stays applied while pill counts (department-only) ignore it.

---

## 3. Every sort function, and each one's bugs

There are exactly **two** sort implementations, plus one dead sort surface.
There is **no name sort anywhere**, despite the option being expected.

### 3.1 Catalogue sort — `catalog.js`

- State: `CatalogView.sortBy`, default `"featured"` (line 12), an in-memory
  static — **not in the URL/hash**, so a full reload, a shared link, or
  back/forward navigation all reset it to `featured`.
- UI: only inside the filter drawer, `catalogSortSelectDrawer`
  (lines 384–387): `featured | price-low | price-high | rating`. Applied in
  `bindDrawerEvents` (line 647: `this.sortBy = sortSel.value`) and only on
  "Show Results" — changing the select alone does nothing.
- Implementation (lines 254–256, after all filters, on a spread copy so the
  master array is not mutated):

```js
if (this.sortBy === "price-low") products.sort((a, b) => a.price - b.price);
else if (this.sortBy === "price-high") products.sort((a, b) => b.price - a.price);
else if (this.sortBy === "rating") products.sort((a, b) => b.rating - a.rating);
```

- Bugs:
  1. **Price comparison is numeric and correct in this dataset** (all prices
     are JSON numbers) — there is no string-vs-number bug here. It would break
     only if a price arrived as a string or `null` (then `a.price - b.price`
     yields `NaN` and sort order becomes arbitrary); nothing coerces or guards
     it, and `originalPrice` is never a sort key.
  2. **`rating` sort is a no-op:** every product's rating is 4.8, so
     `b.rating - a.rating` is always 0 and the grid never visibly changes.
     Users experience this as "sort is broken".
  3. **`featured` is not a sort at all** — it preserves `products.json` file
     order. No tie-breaker is defined for any key, so equal prices/ratings keep
     file order (stable in modern engines, but undocumented and dependent on
     the JSON order, not on popularity — `reviewCount`/`ridersInstalled` are
     never used).
  4. **Sort does apply to filtered/searched results** (it runs after the
     filter pipeline), contrary to one common suspicion — but it is **lost on
     navigation**: leaving the catalogue for a product page keeps the static
     value for the SPA session, while a reload or a fresh link resets it, and
     the home sort (§3.2) never syncs with it.
  5. Sort is applied **before** the skeleton render: the grid is first filled
     with up to 8 skeletons, then replaced after a fixed `setTimeout(…, 120)`
     (`render`, lines ~440–450). Sorting itself is not the delay; the 120 ms
     skeleton flash is.

### 3.2 Home sort — `app.js` lines 471, 602–610

```js
<select id="home-sort-select">
  <option value="featured">Featured</option>
  <option value="low">Price: low to high</option>
  <option value="high">Price: high to low</option>
</select>
…
let items = [...db.getRecommendedProducts(activeBike, null, 8)];
if (sortSelect.value === "low") items.sort((a, b) => a.price - b.price);
if (sortSelect.value === "high") items.sort((a, b) => b.price - a.price);
```

- Bugs: it sorts **only the 8 recommended products**, ignoring whichever
  home filter button is active (it re-fetches the unfiltered recommendation
  list, discarding the filter selection); its option values (`low/high`) differ
  from the catalogue's (`price-low/price-high`) and it never writes
  `CatalogView.sortBy`, so the two sorts are independent and contradictory;
  with a bike selected, `getRecommendedProducts` is empty (§2.3B), so home
  sort sorts nothing.

### 3.3 Home filter buttons — crash, not a sort (`app.js` lines 585–597)

```js
const dept = window.HRz.Catalog.getDepartment(filter);
let filtered = filter === "all"
  ? db.getRecommendedProducts(activeBike, null, 8)
  : baseProducts.filter(p => dept.matches(p)).slice(0, 8);
```

**`Catalog.getDepartment` does not exist anywhere in the codebase** (the only
occurrence of the string is this call site). Clicking any home filter button
other than "All Gear" throws a `TypeError` and the filter never applies (the
button's `active` class is set before the throw, so the UI looks selected while
the grid is unchanged). This is the home-page filter bug, distinct from sorting.

### 3.4 Other orderings (not sorts, but user-visible)

- Search results are ordered by `smartSearch` score only (`utils.js` lines
  254–259); equal scores keep input order, with no price/rating tie-break.
- Product-page related items are same-category-first via
  `getRecommendedProducts` (`db.js` lines 482–514) only when no bike is set.
- Admin catalogue table is file order, paginated 50/page (`admin.js` lines
  ~205–230); no sort control exists there.

---

## 4. Cart: persistence, the reload question, and BUY NOW

**Storage:** `js/cart.js` `CartDrawer` + `js/storage.js` `StorageService`.
The cart is an array of `{id, name, price, image, sku, quantity}` snapshots
(not live product references) stored in **localStorage** under
`hrz_pitstop_app_state_v10` (`storage.js` line 6; `getCart`/`setCart` lines
108–116). `setCart` rewrites the whole app state on every mutation. The badge
is updated from that same store (`updateCartBadge`, lines 123–136, plus a
`MutationObserver` mirror to the mobile dock in `app.js` lines 165–173).
`addItem` (lines 79–105) increments `quantity` if the id already exists, else
pushes; `updateQuantity` (lines 107–121) removes at ≤ 0. There is **no
sessionStorage cart and no in-memory-only cart** — on the code as written, a
plain reload should *not* empty the cart.

**So why would a user see the cart vanish on reload? The code gives four
real mechanisms, and one non-mechanism to rule out:**

1. **Checkout clears it unconditionally** (`checkout.js` lines ~196–205):
   `Storage.setCart([])` runs *before* the popup-blocked branch is decided, so
   a blocked WhatsApp popup still empties the cart while the user believes the
   order did not go through.
2. **The login gate eats the first add after every reload.** `cart.js`
   `bindEvents` (lines 16–43): if not logged in and the in-memory flag
   `CartDrawer.add_to_bag_login_prompted` is not set, the add is diverted to
   `Auth.showLoginPopup`. That flag is in-memory only, so it resets on every
   reload; dismissing the popup (×, backdrop, Esc) runs `onCancel`, shows
   `"Sign in or guest mode required to add items"` and **discards the item**.
   A user who reloads, taps "+ Bag", and closes the popup sees an empty bag.
3. **Auth itself is sessionStorage** (`auth.js` lines 18–29, key
   `hrz_auth_user_v1`), so login state — but not the cart — dies when the tab
   closes; combined with (2) this makes the post-reload experience feel like
   the cart was lost.
4. **Storage failure is silent-ish:** `saveState` catches quota errors and
   only toasts (`storage.js` lines 68–76). The DB cache writes in
   `db.js _persist()` compete for the same ~5 MB localStorage quota; if the
   quota is full, cart writes fail while the UI still shows the "Added … to
   bag" toast.
5. **Ruled out:** `DB.init()`'s `cleanupLegacyKeys` does *not* delete the cart
   key — `hrz_pitstop_app_state_v10` is explicitly protected
   (`storage.js` lines 33–51, `db.js` line ~288). A reload-vanish that survives
   (1)–(4) above needs a live-browser check (private mode, a different
   origin/port, or cleared site data would all do it); it is **not**
   reproducible from `cart.js`/`storage.js` alone. This is flagged, not
   papered over.

**BUY NOW (`product.js` lines ~490–515):** it does **not** create a duplicate
line item — it calls the same `CartDrawer.addItem(pCopy)`, which increments
quantity if the id is already present — and then, after a fixed 100 ms
`setTimeout`, sets `window.location.hash = "checkout"`. Consequences:

- If the product is already in the bag, BUY NOW silently makes it quantity 2
  (or more on repeat clicks) instead of a clean single-item checkout — this is
  the "duplicate" users report; it is a quantity increment, not a second row,
  except for variant products, where the id is suffixed per colour
  (`pCopy.id + "-" + colour`, lines ~470–480) so the same product in two
  colours *does* become two rows.
- If not logged in, BUY NOW first shows the login popup; only on success does
  it add and navigate. Dismissing the popup adds nothing and navigates
  nowhere.
- If the item is the first in the bag, `addItem` **opens the cart drawer**
  (lines 93–95: `if (isFirstItem) this.openCart()`), and the 100 ms later
  navigation to `#checkout` does not close it — the drawer can sit on top of
  the checkout view (route changes never call `closeAllPanels`).
- The cart drawer's own checkout button (`cart.js` lines ~200–215) re-prompts
  for login every time when logged out (it does not use the
  `add_to_bag_login_prompted` flag), then closes the drawer and goes to
  `#checkout`. Its label in `index.html` line 194 is **"Secure checkout →"**
  — see §5 on why that wording is misleading.

Other cart notes: free-shipping progress uses threshold ₹2,999
(`FREE_SHIPPING_THRESHOLD`, line 8) matching checkout's shipping rule; prices
in cart snapshots are frozen at add-time and never re-validated against the
catalogue; removing an item uses `updateQuantity(id, -999)`.

---

## 5. Checkout and WhatsApp handoff

**Module:** `js/checkout.js` `CheckoutView.render()` (lines 8–219).
If the cart is empty it renders an empty-state card; otherwise:

- **Form:** name, phone (`pattern="[0-9+ ]{10,14}"`), email, address, city,
  PIN (`pattern="[0-9]{6}"`, digits-only on input) — all `required`, but no
  server validation exists anywhere; validation is browser-native only.
- **Totals:** `subtotal = Σ price × quantity`; shipping ₹0 at ≥ ₹2,999 else
  ₹199; grand total = subtotal + shipping. No tax line, no coupon/discount
  application (the stored `appliedCoupon` in `storage.js` is never read by
  checkout), no stock re-check.
- **Payment wording:** there is **no payment gateway** — no Razorpay, Stripe,
  or any gateway script, key, or API call anywhere in the site. The payment
  section (lines ~80–105) offers three radio options (UPI/GPay/PhonePe,
  Credit/Debit Card, Cash on Delivery), each captioned *"Confirm details with
  us on WhatsApp"*, under the line (line 82):
  > "Payment will be securely processed via WhatsApp after confirming your
  > order details."
  The word "securely" here describes a WhatsApp chat, not a payment processor;
  combined with the cart drawer's **"Secure checkout"** button
  (`index.html` line 194) and the home service strip's "Safe payments · Cards ·
  UPI · Wallets" (`app.js` line ~554), the site implies card/UPI processing
  that does not exist. The help page (`app.js` lines ~1341+) likewise claims
  cards/UPI/COD are accepted.
- **WhatsApp handoff — yes, the cart is pre-filled, in full** (lines ~175–195):

```js
const waUrl = `https://wa.me/?text=${encodeURIComponent(waText)}`;
// waText includes: customer name/phone/email/address+PIN, payment method,
// bike fitment string, then per item "1. <name> (Qty: n) - ₹<line total>"
// plus "   SKU: <sku>" when present, then "*Grand Total:* ₹<total>"
const popup = window.open(waUrl, "_blank");
```

  Two defects: (a) the URL is `https://wa.me/?text=…` **with no phone number**,
  so it opens WhatsApp's generic share/chooser instead of the store's number
  (the floating button in `index.html` lines 161–162 has the same defect — a
  generic greeting, no number); (b) the order is saved locally and the cart
  cleared **regardless of whether the popup opened** (see §4, mechanism 1).
  If the popup is blocked, a fallback card with an "Open WhatsApp" link is
  shown, but the cart is already empty and the order already recorded.
- **Order record:** a local order (`HRZ-ORD-<random 5 digits>`,
  `DTDC-<random 8 digits>` tracking id, status `"Pending WhatsApp
  Confirmation"`) is unshifted into `DB.orders` and `_persist()`ed — but per
  §11 C2, `DB.init()` discards persisted orders on the next load, so the
  "recorded" order is session-only in practice (see §9, tracking).
- **Success view** (`renderSuccessView`, lines 221–238): "Order Request
  Recorded! … We will finalize stock, shipping, and payment directly on
  WhatsApp." with buttons to `#tracking` and `#catalog`. There is no
  confirmation that the WhatsApp message was actually sent.

---

## 6. Admin (`admin.js`, 986 lines)

**Route:** `#admin` → `App.handleRoute` → `AdminCMS.render()` (lines 13–87).
**There is no auth check on this route at all** — anyone who navigates to
`#admin` gets the full panel. `storage.js`'s `adminRole: "Admin"` default
(line 17) is never read or enforced anywhere; no password, role, or
`Auth.isLoggedIn()` gate exists in `admin.js` or `app.js`.

**Tabs** (sidebar, lines ~30–70): Hero Offer Banner; Product Catalog (count
badge, 50/page pagination, search by name/SKU/category, category filter pills
stored on `#app.dataset.catalogFilter`); Compatibility Matrix; Reviews
moderation queue (pending badge); Customer Orders (status `<select>` per
order); CSV Import/Export; Audit Logs.

**What it can edit, and what actually sticks:**

| Edit | Code | Persists? |
|---|---|---|
| Hero banner (badge/title/subtitle/bg image, incl. file upload → data-URL) | `bindTabEvents` hero form → `Storage.setHeroBanner()` (`storage.js` lines 151–157) | **Yes** — separate localStorage key, survives reload, and the home hero reads it (`app.js renderHomeView` reads `getHeroBanner()`; note the home hero template itself hard-codes its own copy/headline and does not render the stored banner fields, so the edit's storefront effect is partial — see §11 M3) |
| Add / edit / delete product (name, category incl. a "Create Custom Category" option, price, original price, SKU, sizes, description, image URL/upload, in-stock, visible) | `openAddProductModal` (624+), `openEditProductModal` (763+), `DB.addProduct/updateProduct/deleteProduct` (`db.js` 541–583) | **Session-only.** `_persist()` never writes `products` (comment in code: "PRODUCTS array is too large (~11MB), do not save to localStorage" — the actual file is 1.5 MB). `DB.markCatalogUnsaved()` (lines 529–539) shows a red banner: *"Edit applied in this session only. Click Export JSON and replace data/products.json to make this permanent."* Export JSON downloads the catalogue; nothing applies it automatically. Note `addProduct` invents a SKU (`HRZ-<timestamp>`) when none is given, and defaults new products to rating 5.0 |
| Compatibility rules add/delete | `openAddCompModal` (913+), `DB.add/deleteCompatibilityRule` | Intended to persist via `_persist()`, but **lost on reload** by the §11 C2 cache-key flaw (see below) |
| Review approve/reject | `DB.updateReviewStatus` | Same — lost on reload |
| Order status change | `DB.updateOrderStatus` | Same — lost on reload |
| Compatibility CSV export/import (PapaParse) | `DB.export/importCompatibilityCSV` (`db.js` 626–691) | Export downloads a file; import writes to the in-memory collection + `_persist()` (same reload flaw). Import skips rows whose product+bike pair already exists and requires PapaParse, else throws |
| Audit logs | `Storage.addAuditLog` (`storage.js` 159–168) | Yes (same app-state key), but the log user is hard-coded `"Admin"` and entries are only created for admin/DB actions, not for customer actions |

**The reload flaw (detail):** `_persist()` writes bikes, compatibility, reviews,
orders and bundles to localStorage, but `init()`'s cache branch requires
`cachedProducts` too, and nothing ever writes `hrz_db_products_v31`. So on
every reload the fetch branch runs and **overwrites all six collections from
the JSON files**, discarding every admin edit (including order-status and
review-moderation changes) and every customer order placed in the previous
session. Only the `storage.js` state (cart, wishlist, garage, hero banner,
audit logs, fitment reports) survives a reload.

**Other admin defects:** "Low Stock Alerts" is hard-coded `0`
(`admin.js` line ~215) even though no stock-quantity field exists; the catalog
search input re-renders the whole admin view on every keystroke with a
focus-restoration hack (lines ~480–510); delete confirmations are native
`confirm()`; there is no bulk product CSV import (only compatibility CSV).

---

## 7. Auth (`auth.js`, 175 lines)

- **No real authentication.** `AuthService` stores the user in
  **sessionStorage** (`hrz_auth_user_v1`, lines 18–29), so login dies when the
  tab closes. `isLoggedIn()` is just "a sessionStorage entry exists".
- **"Continue with Google" is a demo button:** it logs in as
  `DEMO_GOOGLE_ACCOUNTS[0]` — Rahul Sharma, `rahul.sharma@gmail.com` — with no
  OAuth redirect, no token, no password (lines 8–14, 100–110). Anyone clicking
  it becomes "Rahul Sharma". The other two demo accounts are never reachable.
- **"Continue as Guest" does not create a user:** the popup's `close(true)`
  path (lines ~90–95) runs the success callback without calling `setUser()`,
  so `isLoggedIn()` stays `false`. Guest therefore works for the single action
  that opened the popup, but the cart-drawer checkout button re-prompts on
  every use (§4), and the header avatar never appears for guests.
- **Popup behaviour:** created dynamically (`showLoginPopup`, lines 38–100),
  closed by ×, backdrop click, or Esc — all of which run `onCancel`, which for
  an add-to-cart flow discards the item (§4). No "remember me", no email
  login, no signup, no password reset, no account page. The avatar menu
  (`_showUserMenu`, lines 132–169) links to `#tracking`, `#wishlist`, `#garage`
  and Sign Out (`logout`, lines 31–36, clears sessionStorage only — cart,
  wishlist and garage survive logout).
- Legal links in the popup point to `#help` for both Terms and Privacy Policy.

---

## 8. Search (`search.js`, 82 lines; scoring in `utils.js` lines 137–260)

- **Live suggestions:** `SearchEngine.init()` binds `#globalSearch` (inside the
  `#searchPanel` overlay, `index.html` lines 199–207) with a 200 ms debounce
  (`utils.js debounce`, lines 97–107). Under 2 characters it clears the
  popover; otherwise it renders up to **5** matches as image + name + category
  + price rows in `#searchAutocomplete`. Clicking a row closes the panel and
  navigates to `#product?id=<id>`; pressing Enter navigates to
  `#catalog?search=<query>`. The search panel itself is opened from the header
  search button / mobile dock (`app.js bindGlobalUI`).
- **Bugs:**
  1. **Dead bike code:** lines 25–27 compute `bikeProducts` and
     `bikeProductIds` and then never use them. Suggestions are **not**
     filtered by the selected bike; `smartSearch` only adds a +10 fitment
     bonus per product, and the catalogue search path passes `activeBike =
     null`, so no fitment effect at all there.
  2. **Token rules lose queries:** single-character tokens are dropped, a
     fixed stop-word list (`and/or/the/for/with/in/of/to/a/an/at/by/from/on/
     all/&`) is stripped, and non-alphanumeric characters are replaced with
     spaces before tokenising — so `"MT-15"` becomes `mt, 15` and `"100%"` becomes
     `100`.
  3. **The `"Missing SKU"` trap:** every product's SKU is `"Missing SKU"` for
     1,464 rows, and `smartSearch` awards +20 for any token contained in the
     SKU string — so searching `missing` or `sku` matches essentially the
     whole catalogue.
  4. **Multi-token penalty produces empty/odd results:** a query is scored
     per token (exact word 35, prefix 24, substring 12; brand/category/
     subcategory word 18/12; SKU 20; bike-compatibility word 10; typo-tolerant
     Levenshtein ≤ 1 only for tokens ≥ 5 chars, +8), then if not all tokens
     matched, `score *= tokensMatched/tokens.length`, and `× 0.3` more if no
     name word matched; only `score ≥ 6` survives, sorted by score with no
     tie-break. Partial matches therefore rank below the threshold more often
     than users expect, and single-token matches (e.g. a brand) can outrank a
     genuinely relevant multi-word product.
  5. **No keyboard navigation** (arrows/Tab through suggestions), no "view all
     results" affordance except Enter, no loading or error state, no
     highlighting of the matched term, and no debounce cancellation — a slow
     keystroke sequence can render stale results. The scorer runs
     `levenshtein` over all 1,747 products per keystroke (debounced), which is
     the site's main client-side cost.
  6. Suggestions show the raw `p.image` with **no `onerror` fallback** (unlike
     cards), so a missing image renders as a broken icon in the popover.
  7. The mobile drawer search (`menu.js` drawerSearchInput) bypasses
     suggestions entirely and goes straight to `#catalog?search=…`.

---

## 9. Product pages, garage, wishlist, recently viewed, reviews, orders, FAQ/help, newsletter, fitment report

- **Product page** (`product.js render`, lines 248–531): gallery (main image
  with hover zoom on desktop, swipe carousel on mobile, thumbnail strip, and a
  fullscreen viewer with keyboard/swipe navigation), category + SKU badge,
  title, star rating, price + original price, fitment banner, Add to Bag /
  Buy Now (§4), trust pills, highlights list, "Didn't Fit My Bike?" link.
  Broken or demo-only parts:
  - Reviews shown are `DB.getReviews()` filtered to this product id and
    `status === "published"` — the 3 seeded reviews reference demo ids, so
    **no real product ever shows a review**; the page instead shows
    *"No reviews published yet…"*. The review *count* displayed next to the
    stars is `reviews.length` (0), while the card/grid star line uses the
    product's own `rating` (always 4.8) and `reviewCount` (8/12) — the two
    numbers on the same page disagree.
  - "Customer Installation Gallery" is hard-coded fake content: the product's
    own image captioned "Himalayan 450 Summit — Installed by Rahul M. ·
    Bengaluru" plus `images/crash_guard_product.webp` captioned "Duke 390
    Gen-3 — Installed by Ankit S. · Pune", for **every** product.
  - `product.description`, `product.sizes`, `product.authenticity`,
    `product.warranty` are rendered only if present; they are absent on all
    1,747 rows, so those blocks never appear and the fallbacks
    `"100% OEM Certified"` / `"12 Months Warranty"` are shown instead.
  - Variant UI (`bindVariantEvents`, lines 604–657) only activates for the 33
    rows with `variants`; the variant original price is **fabricated** as
    `Math.round(v.price * 1.15)` rather than read from `v.originalPrice`.
  - Related products are empty whenever a bike is selected (§2.3B).
  - Unknown id renders a "Product Not Found or Unavailable" card (not a 404,
    and the URL stays on the bad id).
- **Garage** (`garage.js`): bike picker modal (brand → model → variant, plus
  preset chips) writes via `Storage.setActiveBike()` (which also appends to the
  garage list) and navigates to `#garage`. Defects: changing the variant
  `<select>` calls `selectBike()` **immediately** (line ~205), and a
  single-variant model auto-submits on model change (lines ~185–195), so the
  "Set Active Bike" button is often bypassed; `selectBike` always navigates to
  `#garage` after 250 ms even when invoked from the garage's own "Set Active"
  button; `removeBikeFromGarage` (`storage.js` lines 99–107) matches on
  `bikeId`, but garage entries built by some paths carry no stable `bikeId`
  (preset fallback builds `bike-<brand>`), so removal can silently fail; and
  the garage "recommendations" are empty with a bike selected (§2.3B).
- **Wishlist** (`app.js renderWishlistView`, lines 873–903; toggles in
  `storage.js` lines 131–145 and `catalog.js bindCardEvents`): id list in
  localStorage, renders via `renderProductCard`, count badge in the header.
  Works as designed; it is **not** gated by login, unlike the cart.
- **Recently viewed** (`storage.js` lines 118–129; home section in
  `app.js`): last 10 product ids, newest first, added on every product-page
  render — including on a "Product Not Found" render, since
  `addRecentlyViewed(productId)` runs before the existence check
  (`product.js` lines 249–253), so dead ids accumulate and are filtered out
  only at render time. Home falls back to the first 4 bestsellers when empty.
- **Reviews view** (`app.js renderReviewsView`, lines 1284–1314): lists the 3
  seeded published reviews (all demo-product reviews). There is **no
  customer review submission form anywhere** — reviews can only appear via
  admin moderation of seeded rows or by editing JSON. The home review
  carousel (`getReviewCards`, lines 838–871) hard-codes ★★★★★ for every card
  regardless of the review's actual rating.
- **Orders tracking** (`app.js renderTrackingView` lines 987–1048 and
  `openOrderDetailsModal` lines 1050–1283): lists `DB.getOrders()` with a
  4-step timeline (Ordered → Processing → Shipped → Delivered) derived from
  status substrings, plus a detail modal. Demo-only in practice: the 2 seeded
  orders reference demo product ids and a Bengaluru address; new orders from
  checkout are lost on reload (§6/§11 C2); status `"Pending WhatsApp
  Confirmation"` matches **no** timeline branch, so a just-placed order shows
  0% progress with only "Ordered" marked; there is no courier tracking link
  or lookup by order id — the page shows every order in the local store to
  every visitor.
- **FAQ / Help** (`app.js renderHelpView`, lines 1316–1368; home FAQ section):
  static `<details>` accordions (fitment guarantee, shipping, fitment report,
  payment methods, international shipping, terms, privacy, returns). No search,
  no contact form, no ticket flow — the only contact routes are the
  `mailto:support@hrzpitstop.com` footer link and the WhatsApp float button.
  Several answers contradict the code (e.g. "our catalog filters only items
  engineered for that model" — the catalogue does not filter by bike, §2.3B).
- **Newsletter** (home, `app.js` lines ~590–600): a form that on submit only
  resets itself, sets *"You're on the list — welcome to the ride."* and toasts
  "Subscribed successfully!" — **no network request, no stored subscriber**.
  Purely demo.
- **Fitment-report form** (`product.js openFitmentReportModal`, lines
  533–602): bike variant (read-only), issue-type select, free-text details.
  On submit it closes and toasts *"Fitment report submitted. Our technical
  team will reach out within 2 hours with a return waybill."* — **but nothing
  is saved**: the report is not written to `Storage.fitmentReports` (the key
  exists in `storage.js` defaults but has no writer/reader anywhere), not
  sent anywhere, and not visible in admin. The "2 hours / return waybill"
  promise is therefore unfounded. The same pattern (toast as success) is used
  by the newsletter.
- **Bundles** (`data/bundles.json`, 2 kits): loaded into `DB.bundles` and
  exposed via `getBundles()`, but **never rendered anywhere** — no bundle
  section, card, or cart path references them.
- **Models view** (`app.js` lines 1369–1402): brand → model cards from
  `menu.js menuData.shopByBike`, images via `image_map.js` (see §10), click →
  `#catalog?search=<model>` (§2.3A). Brand keys are case-sensitive
  (`menuData.shopByBike[brand]`), so a differently-cased `?brand=` yields an
  empty grid with no message.
- **About / Events** (`menu.js` lines 958–1270): static marketing copy with
  hard-coded claims (50,000+ riders, 250+ models, named brands) and event
  cards; no data behind them.

---

## 10. Image handling (`image_map.js`, 111 lines)

- `image_map.js` is **only a bike/brand image map** (keys like `"Himalayan 450"`,
  `"Duke 390 Gen-3"`, brand logos) used by the home bike slider and the models
  view. It contains **no product-image mapping**; product images come straight
  from `products.json` (`images_processed/catalog/<brand>/<file>.webp`).
- **When a product image file is missing, the layout does not collapse — but
  the fallback chain fails too, in this zip:**
  - Cards (`catalog.js` line 710), cart rows (`cart.js` line 167), product
    main/carousel/variant images (`product.js` lines 301, 305, 328, 646),
    order thumbnails (`app.js` lines 1027, 1166) and admin thumbnails
    (`admin.js` line 248) all use
    `onerror="this.src='images/helmet_product.webp'"`.
  - `images/helmet_product.webp` lives in `images/`, which is **absent from
    this zip**, so the fallback 404s as well and the browser shows its broken-
    image icon inside the fixed-size media frame. The card/grid does not
    break structurally (the `<img>` box keeps its size), but every product
    visual is a broken icon.
  - Gaps in the fallback: thumbnail-strip images on the product page, gallery
    viewer image, search-suggestion images and menu-card images have **no**
    `onerror` at all, so they show broken icons with no recovery.
  - `image_map.js` values point at `images/bikes/*.jpg`, then the code rewrites
    them to `*_transparent.png` (`app.js` lines ~416, ~1390) — a file that
    does not exist in the map or the zip — before falling back to
    `images/bike_t_<n>.webp` (also absent). Bike imagery is therefore broken
    at every level of fallback in this zip.
  - The home page additionally references `images/hero-rider.webp`,
    `images/hero_banner.webp`, `images/category_*.webp` and four
    `images/cat_vid_*.mp4` videos, and the header/logo references a long
    `images/HRZ_BIKE_LOGO_…webp` filename — all in the missing `images/`
    folder. There is no placeholder component, no lazy-load error state, and
    no `srcset`/responsive image strategy anywhere.

---

## 11. Prioritised bug list

### Critical (breaks core shopping or trust)

- **C1 — Home filter buttons crash.** `app.js:588` calls
  `Catalog.getDepartment(filter)`, which does not exist. Any home filter other
  than "All Gear" throws and leaves the grid unchanged while showing the
  button as active.
- **C2 — All DB persistence is discarded on reload.** `db.js _persist()`
  (364–376) never writes `hrz_db_products_v31`, but `init()` (296–306) requires
  it to use the cache. Every reload re-fetches all six JSON files, wiping
  admin product/compatibility/review/order edits and every checkout order.
  Only `storage.js` state (cart, wishlist, garage, hero banner, audit logs)
  survives. This is also why order tracking cannot work across sessions.
- **C3 — Bike fitment returns nothing, and the catalogue ignores it.**
  `db.js getProductsForBike()` / `checkFitment()` (476–480, 392–474) cannot
  match any real product (no `bike_compatibility` field; `compatibility.json`
  references only demo ids), so home/garage/related results empty out when a
  bike is chosen — while `catalog.js render()` never applies the bike filter
  at all. The site's central "guaranteed fitment" promise is unimplemented
  for the real catalogue.
- **C4 — Shop-by-Bike / model / many menu links land on "No Parts Found".**
  `menu.js` links and `app.js renderModelsView()` route bike models to
  `#catalog?search=<model>`, but `smartSearch` (`utils.js` 137–260) has no bike
  field to match against (§2.3A). Same root cause as C3, different surface.
- **C5 — Admin is ungated.** `app.js` `case "admin"` renders `AdminCMS` with
  no login, password or role check; `storage.js adminRole` is never enforced.
  Anyone can edit/delete the catalogue, orders and reviews from the URL.
- **C6 — Checkout clears the cart even when WhatsApp fails, and has no
  payment processing.** `checkout.js` ~196–205 (`setCart([])` before the
  popup-blocked branch); `wa.me/?text=…` with no store number (line 190);
  "Secure checkout" (`index.html:194`) and "Payment will be securely
  processed via WhatsApp" (`checkout.js:82`) imply a gateway that does not
  exist.
- **C7 — All product imagery is missing in this zip and the fallback is
  missing too.** Every `image`/`gallery` path is under the absent
  `images_processed/`; every `onerror` fallback points at the absent
  `images/helmet_product.webp` (§10). The storefront is visually broken until
  the image folders are restored or a real placeholder is shipped.
- **C8 — "Google login" is a hard-coded demo account.** `auth.js:8–14,
  100–110`: any visitor becomes Rahul Sharma; there is no OAuth, and guest
  mode does not create a session, so every cart/checkout gate re-prompts.

### High (major feature broken or misleading)

- **H1 — Catalogue data is placeholder-grade.** All ratings 4.8, reviewCounts
  8/12, `inStock` always true, 1,464 `"Missing SKU"` values, 183 blank
  subcategories, no descriptions/sizes/badges. Sorting by rating is a no-op
  (§3), "4.8★ (8 reviews)"-style social proof is identical on all 1,747 cards,
  and stock/urgency displays cannot be trusted.
- **H2 — Product-page proof sections are fabricated.** Hard-coded
  installation captions (`product.js` ~§9), zero real reviews reachable (all
  seeded reviews reference demo ids), and review-count disagreement between
  the product header and the reviews section.
- **H3 — Fitment reports and newsletter are toast-only.** `product.js
  533–602` (report never stored/sent despite the "2 hours / return waybill"
  promise) and `app.js` newsletter (no request, no storage). `storage.js`
  `fitmentReports` has no writer.
- **H4 — BUY NOW increments instead of checking out cleanly.**
  `product.js` ~490–515 + `cart.js addItem` (79–105): existing item becomes
  quantity 2+; first-item opens the cart drawer which is never closed before
  the 100 ms navigation to checkout; variant colours create separate rows.
- **H5 — Cart/login gate discards items.** `cart.js:16–43`: dismissing the
  login popup on the first post-reload add drops the item; the in-memory
  `add_to_bag_login_prompted` flag resets every reload.
- **H6 — Sort state is not shareable or durable.** `catalog.js:12`
  `sortBy` is in-memory only (not in the hash); home sort (`app.js:602–610`)
  is a separate, incompatible implementation that sorts only 8 items and
  discards the active home filter. No name sort exists.
- **H7 — Reset Filters does not reset search/category.**
  `catalog.js` empty-state button (lines 363, 478–486) leaves `searchQuery` intact, so
  the commonest empty state cannot be escaped with the provided button.
- **H8 — Colour filter requires variants (33 rows).** Selecting any colour
  empties ~98% of the catalogue (`catalog.js` colour filter).
- **H9 — Order timeline cannot represent a new order.** `"Pending WhatsApp
  Confirmation"` matches no branch in `app.js getOrderTimelineHTML`
  (916–985), so a just-placed order shows 0% progress; tracking shows all
  local orders to all visitors with no lookup.

### Medium

- **M1 — Search suggestions ignore the bike and have dead code.**
  `search.js:25–27` (`bikeProducts`/`bikeProductIds` computed, unused); no
  keyboard navigation; no `onerror` on suggestion images; `Missing SKU`
  token bonus (§8).
- **M2 — Home bike slider never actually selects a bike.**
  `app.js` bike items carry no `data-brand`/`data-model`, but `activateBike`
  (lines ~660–700) reads `el.dataset` and returns early without them; the
  slider's scroll/filter timer therefore never runs, and only the click →
  `#models` path works.
- **M3 — Hero banner edit only partly reaches the storefront.**
  `storage.js setHeroBanner()` persists, but `app.js renderHomeView()`'s hero
  markup hard-codes its own headline/copy and only the stored banner object
  is read, not rendered, in the hero section.
- **M4 — Five categories are pill-less** (58 products, §2.3C); pill counts
  ignore search/filters, so counts disagree with the grid.
- **M5 — Variant original price is fabricated** (`product.js
  bindVariantEvents`: `Math.round(v.price * 1.15)`) instead of using
  `v.originalPrice`.
- **M6 — Recently-viewed records dead ids** (`product.js:249–253` runs before
  the product-exists check).
- **M7 — Garage removal can silently fail** (`storage.js:99–107` matches on
  `bikeId`, which preset-fallback entries do not reliably carry); variant
  change auto-submits (`garage.js` ~185–210), bypassing the confirm button.
- **M8 — Admin "Low Stock Alerts: 0" is hard-coded** (`admin.js` ~215) and no
  stock-quantity field exists; admin search re-renders on every keystroke.
- **M9 — Bundles are loaded but never shown** (`db.js getBundles()` has no
  caller that renders).

### Minor / polish

- **m1 — Demo layer still ships:** `DEFAULT_*` constants, `DEMO_PRODUCT_GROUPS`
  and commented-out demo merge in `db.js`; demo ids referenced by
  `compatibility.json`, `reviews.json`, `orders.json`, `bundles.json`.
- **m2 — SEO canonicals use `?view=` query params while routing uses hashes**
  (`seo.js updateCanonicalURL`), so canonical URLs do not match real routes;
  JSON-LD brand is hard-coded "HRz Pitstop" even for branded products, and
  `priceValidUntil` is a fixed 2027-12-31.
- **m3 — `getWikiImage` (`app.js:351–366`) fetches Wikipedia thumbnails but
  has no caller in the current render paths.**
- **m4 — Skeleton flash:** catalogue grid renders skeletons then replaces
  them after a fixed 120 ms timeout, regardless of actual readiness.
- **m5 — Home review carousel hard-codes ★★★★★** (`app.js getReviewCards`)
  irrespective of stored ratings.
- **m6 — `quickView` section (`index.html:210`) is never populated**; the
  overlay/panel history dance (`pushState({panelOpen:true})` in cart, viewer,
  modals, menus) can require multiple back-presses to leave a view.
- **m7 — No coupon path:** `appliedCoupon` is stored but never applied in
  cart or checkout; shipping copy ("taxes calculated at checkout",
  `index.html:192`) contradicts checkout (no tax line).
- **m8 — Accessibility/robustness gaps:** filter drawer and mega-menu rely on
  click-only toggles; search suggestions have no keyboard support; several
  inline `onclick` handlers and unescaped interpolations in home/models
  templates (brand/model names) bypass the `escapeHTML` used elsewhere.

---

## 12. Routing / view model (`app.js`)

**Model:** hash routing over static sections — no framework, no server routes.
`index.html` lines 106–119 define 13 empty `<section class="view">` elements
(`home, models, catalog, product, garage, checkout, tracking, reviews, help,
wishlist, admin, about, events`); `css/layout.css:6–7` hides all `.view` and
shows only `.view.active`. The cart drawer, search panel, mega-nav, side menu
drawer, modals and mobile dock live **outside** `#app` and are shown/hidden by
CSS classes independently of the route — which is why drawers can linger over
a new view (§4).

**Lifecycle** (`App.init`, lines 9–26): `await DB.init()` → data-load banner
sync → `Garage.init(onBikeChanged)` → `Cart.init()` → `Search.init()` →
`Auth.init()` → `Menu.init()` → `hashchange` listener + `bindNavigation()` +
`bindGlobalUI()` → initial `handleRoute()`. `onBikeChanged` (lines 28–33)
re-runs routing only when the current view is `home`/`catalog`/empty — so a
bike change made while on a product, garage or checkout page does **not**
refresh that view (garage navigates to itself via `selectBike`'s hash set).

**`handleRoute()` (lines 212–348):**

1. Splits `location.hash` into route + `URLSearchParams` query string.
2. Toggles `.active` on header nav links (`data-view`) and mobile dock items
   (`data-dock`).
3. Maps department slugs to the single `#catalog` section
   (`deptRoutes` list, lines ~232–235: `helmets, riding-gears, riding-gear,
   jackets, protection, crash-guards, luggage, lights, lighting, performance,
   maintenance`) — note `crash-guards` and `jackets` are recognised routes but
   have no pill slug pointing at them, and `maintenance` is a route but its
   pill slug is also `maintenance` (consistent) while `riding-gears`' pill
   slug is `riding-gears` (consistent) — the inconsistency is in the
   *category argument* each route passes (`"Protection"`, `"Riding Gears"`,
   `"Luggage"`, `"Lights"`, `"Maintenance"`), which only works because
   `normalizeCategory` collapses them.
4. Hides all `#app .view`, shows `#<viewId>` (falling back to `#home` for an
   unknown id), scrolls to top, forces the footer visible, updates SEO.
5. Dispatches by route to the section renderers: `renderHomeView`,
   `renderModelsView(brand)`, `Catalog.render({category, subcategory, search})`,
   `Product.render(id, color)`, `Garage.renderGarageView`,
   `Checkout.render`, `Admin.render`, `renderWishlistView`,
   `renderTrackingView`, `renderReviewsView`, `renderHelpView`,
   `Menu.renderAbout`, `Menu.renderEvents(tab)`; **unknown routes fall through
   to `renderHomeView` with the home section active but the URL unchanged**
   (no 404 view, no redirect).
6. Every render **replaces its section's `innerHTML` wholesale** and re-binds
   events — there is no component state preservation, no transition, and no
   scroll restoration. Query params are the only per-view state that survives
   navigation, and sort/filter state (except category/subcategory/search, and
   only when encoded in the hash) does not.

**Navigation entry points:** header nav (`data-view`, `app.js bindNavigation`
lines 35–64), footer hash links, mobile dock (`data-dock`), mega-menu and side
drawer (`menu.js navigateTo()`, lines 890–949, which closes drawers and
`replaceState`s away the `panelOpen` history entry before setting the hash),
home category tiles and bike slider (plain `location.hash` assignments), and
`data-view-target`/`data-filter` buttons (which build
`#catalog?category=<filter>` — but no current template in `index.html` sets
`data-filter`, so that path is currently unreachable from the static markup).

**Panels vs history:** cart drawer, gallery viewer, fitment modal, order modal,
search panel and menu drawer each `pushState({panelOpen: true})` when opened
and `history.back()` when closed, with `popstate` handling in
`app.js bindGlobalUI` (lines 66–125) to close whichever is open. Because several
panels share the single `panelOpen` flag, opening two panels then pressing
Back can close the wrong one or require extra presses; `closeAllPanels` has
three different history behaviours controlled by `(isPopState, skipHistory)`
flags that differ per caller.

---

## Appendix — CSS structure (skimmed, not line-audited)

12 stylesheets, all linked from `index.html`: `base.css` (tokens/reset),
`header.css`, `menu.css` (1,233 lines — mega-nav + drawer, the largest),
`layout.css` (1,099 lines — views, grids, hero, catalogue layout),
`product.css` (931 lines — detail page, gallery viewer, reviews),
`cart.css`, `orders.css`, `garage.css`, `admin.css`, `auth.css`, `footer.css`,
`responsive.css` (495 lines — mobile dock shown only at the mobile breakpoint,
`.desktop-only`/`.mobile-only` swaps, product-media aspect-ratio override for
non-home views at line ~220). No CSS build step, no variables file beyond
`base.css`; view switching is purely `.view` / `.view.active` display toggling
(`layout.css:6–7`). A noted CSS-side hiding: `.catalog-sidebar { display: none
}` (`layout.css:802`) — the old static sidebar is dead CSS, replaced by the
filter drawer. Responsive behaviour was not verified in a browser.

---

*End of audit. Files reviewed read-only; the only file written was this
`AUDIT.md`.*
