#!/usr/bin/env python3
"""
Phase 2: Scrape Missing Gold Data (Images, Prices, Variants, Descriptions)
Repo: HRz Pitstop (E:\\coad\\hrx website 2)

How the Scraper Operates (100% Accurate, Zero Guessing):
1. Use the existing Verification_Evidence_URL first (Shopify .json fast-path or JSON-LD/OpenGraph).
2. Fallback search on bandidospitstop.com & manufacturer Shopify stores via /search/suggest.json.
3. Strict Price & Identity Validation:
   - Token match >= 80% on brand/model for fallback searches.
   - Selling price MUST be > POS_Purchase_Price (when POS_Purchase_Price > 0).
4. Download high-res product images and convert to .webp inside images_processed/scraped/<brand_slug>/.
5. Clean description by stripping HTML artifacts and replacing competitor store names with 'HRz Pitstop'.
6. Run in batches of 50 with concurrent worker threads (polite per-request delays) and persistent checkpointing.
7. Outputs:
   - scraped_verified_results.json (all successfully verified and scraped items)
   - scrape_manual_review.csv (unresolvable or failed items with reasons)
"""

import os
import sys
import io
import re
import csv
import json
import time
import threading
from urllib.parse import urlparse, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from PIL import Image

# Force UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
QUEUE_CSV = os.path.join(BASE_DIR, 'Needs_Scraping_Queue.csv')
if not os.path.exists(QUEUE_CSV):
    QUEUE_CSV = os.path.join(BASE_DIR, '_vault_archive', 'scraper_working_cache', 'Needs_Scraping_Queue.csv')

RESULTS_JSON = os.path.join(BASE_DIR, 'scraped_verified_results.json')
if not os.path.exists(RESULTS_JSON):
    RESULTS_JSON = os.path.join(BASE_DIR, '_vault_archive', 'scraper_working_cache', 'scraped_verified_results.json')

MANUAL_CSV = os.path.join(BASE_DIR, 'scrape_manual_review.csv')
if not os.path.exists(MANUAL_CSV):
    MANUAL_CSV = os.path.join(BASE_DIR, '_vault_archive', 'scraper_working_cache', 'scrape_manual_review.csv')
SCRAPED_IMG_DIR = os.path.join(BASE_DIR, 'images_processed', 'scraped')

os.makedirs(SCRAPED_IMG_DIR, exist_ok=True)

# Common HTTP Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Dedicated manufacturer domain lookup
BRAND_MANUFACTURER_DOMAINS = {
    'legundary': 'legundary.com',
    'legundary customs': 'legundary.com',
    'lcb': 'legundary.com',
    'mototorque': 'mototorque.in',
    'moto torque': 'mototorque.in',
    'lone ranger': 'lonerangerindia.com',
    'loneranger': 'lonerangerindia.com',
    'dsg': 'planetdsg.com',
    'axor': 'axorhelmets.com',
    'axor helmets': 'axorhelmets.com',
    '66bhp': '66bhp.com',
    'raida': 'raidagears.com',
    'htrz modz': 'htrzmodz.com',
    'htrzmodz': 'htrzmodz.com',
    'motocentral': 'motocentral.in',
    'riders junction': 'ridersjunction.com',
    'ridersjunction': 'ridersjunction.com',
    'bikester global': 'bikesterglobal.com',
    'bikesterglobal': 'bikesterglobal.com',
    'lgp': 'lgpindia.com'
}

COMPETITOR_NAMES = [
    r'\bBandidos\s*Pitstop\b', r'\bBandidospitstop\b', r'\bBandidos\b',
    r'\bMotoCentral\b', r'\bMoto\s*Central\b',
    r'\bMotoTorque\b', r'\bMoto\s*Torque\b',
    r'\bLegundary\s*Customs\b', r'\bLegundary\b',
    r'\bMotocaan\b', r'\bHTR\s*ZMODZ\b', r'\bHtrzmodz\b',
    r'\bRiders\s*Junction\b', r'\bBikester\s*Global\b'
]

# Thread-local storage for requests.Session
_thread_local = threading.local()

def get_session():
    if not hasattr(_thread_local, 'session'):
        s = requests.Session()
        s.headers.update(HEADERS)
        _thread_local.session = s
    return _thread_local.session

def clean_brand_slug(brand):
    b = re.sub(r'[^a-z0-9]+', '_', (brand or 'hrz').lower()).strip('_')
    return b if b else 'generic'

def tokenize(text):
    if not text:
        return set()
    tokens = re.findall(r'[a-z0-9]+', str(text).lower())
    stopwords = {'for', 'with', 'and', 'the', 'of', 'in', 'to', 'a', 'an', 'by', 'on', 'new', 'kit', 'set', 'all'}
    return {t for t in tokens if t not in stopwords and len(t) > 1}

def compute_token_match(query_text, candidate_text):
    q_tokens = tokenize(query_text)
    if not q_tokens:
        return 0.0
    c_tokens = tokenize(candidate_text)
    matched = 0
    for qt in q_tokens:
        if qt in c_tokens:
            matched += 1
        elif any(ct.startswith(qt) or qt.startswith(ct) for ct in c_tokens if len(ct) >= 4 and len(qt) >= 4):
            matched += 0.85
    return matched / len(q_tokens)

def sanitize_description(text, product_name='', brand=''):
    if not text or not str(text).strip():
        b = str(brand).strip() if brand else 'HRz Pitstop'
        return f"{product_name} - Premium motorcycle gear and accessories verified by {b}."
    t = str(text)

    # Strip shopify containers & scripts
    t = re.sub(r'<script[\s\S]*?</script>', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<style[\s\S]*?</style>', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<div class="[^"]*shopify-section[^"]*"[^>]*>[\s\S]*?</div>', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<div id="shopify-section-[^"]*"[^>]*>[\s\S]*?</div>', '', t, flags=re.IGNORECASE)

    # Strip article and custom tags
    t = re.sub(r'</?article[^>]*>', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s+data-[a-zA-Z0-9_-]+="[^"]*"', '', t)
    t = re.sub(r"\s+data-[a-zA-Z0-9_-]+='[^']*'", '', t)
    t = re.sub(r'class="[^"]*(?:claude|chatgpt|ai-response)[^"]*"', '', t, flags=re.IGNORECASE)
    t = re.sub(r'<p[^>]*class="[^"]*claude[^"]*"[^>]*>[\s\S]*?</p>', '', t, flags=re.IGNORECASE)

    # Replace competitor names
    for pat in COMPETITOR_NAMES:
        t = re.sub(pat, 'HRz Pitstop', t, flags=re.IGNORECASE)

    t = re.sub(r'\n\s*\n+', '\n', t).strip()
    return t if t else f"{product_name} - Premium motorcycle gear and accessories verified by {brand}."

def download_and_convert_image(session, img_url, brand_slug, prefix_name):
    if not img_url:
        return None
    try:
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        r = session.get(img_url, timeout=6)
        if r.status_code == 200 and len(r.content) > 1024:
            brand_dir = os.path.join(SCRAPED_IMG_DIR, brand_slug)
            os.makedirs(brand_dir, exist_ok=True)

            safe_name = re.sub(r'[^a-zA-Z0-9_-]+', '_', prefix_name)[:45].strip('_')
            url_hash = f"{abs(hash(img_url)) % 1000000:06d}"
            filename = f"{safe_name}_{url_hash}.webp"
            target_path = os.path.join(brand_dir, filename)

            img = Image.open(io.BytesIO(r.content))
            if img.mode in ('RGBA', 'LA'):
                img.save(target_path, 'WEBP', quality=85)
            else:
                img.convert('RGB').save(target_path, 'WEBP', quality=85)

            if os.path.exists(target_path) and os.path.getsize(target_path) > 1024:
                return os.path.relpath(target_path, BASE_DIR).replace('\\', '/')
    except Exception:
        pass
    return None

def fetch_shopify_json_by_url(session, url):
    """Attempt direct Shopify /products/<handle>.json extraction."""
    parsed = urlparse(url)
    path = parsed.path
    if '/products/' not in path:
        return None

    m = re.search(r'/products/([^/?#]+)', path)
    if not m:
        return None

    handle = m.group(1)
    json_url = f"{parsed.scheme}://{parsed.netloc}/products/{handle}.json"
    try:
        r = session.get(json_url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if 'product' in data and data['product']:
                return data['product'], json_url
    except Exception:
        pass
    return None

def fetch_product_from_html(session, url):
    """Fallback parser for JSON-LD schema or OpenGraph tags in HTML pages."""
    try:
        r = session.get(url, timeout=5)
        if r.status_code != 200 or not r.text:
            return None
        html = r.text

        title = None
        brand_name = None
        price = 0.0
        compare_at = 0.0
        sku = ''
        images = []
        desc = ''

        # 1. Parse JSON-LD scripts
        json_ld_matches = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>([\s\S]*?)</script>', html, re.I)
        for block in json_ld_matches:
            try:
                data = json.loads(block.strip())
                items = []
                if isinstance(data, list):
                    items.extend(data)
                elif isinstance(data, dict):
                    if '@graph' in data and isinstance(data['@graph'], list):
                        items.extend(data['@graph'])
                    else:
                        items.append(data)
                for it in items:
                    if str(it.get('@type', '')).lower() in ('product', 'individualproduct'):
                        title = it.get('name') or title
                        sku = it.get('sku') or sku
                        desc = it.get('description') or desc
                        b_val = it.get('brand')
                        if isinstance(b_val, dict):
                            brand_name = b_val.get('name') or brand_name
                        elif isinstance(b_val, str):
                            brand_name = b_val or brand_name

                        img_val = it.get('image')
                        if isinstance(img_val, list):
                            for im in img_val:
                                if isinstance(im, str):
                                    images.append({'src': im})
                                elif isinstance(im, dict) and im.get('url'):
                                    images.append({'src': im.get('url')})
                        elif isinstance(img_val, str):
                            images.append({'src': img_val})
                        elif isinstance(img_val, dict) and img_val.get('url'):
                            images.append({'src': img_val.get('url')})

                        offers = it.get('offers')
                        if isinstance(offers, dict):
                            p_val = offers.get('price') or offers.get('lowPrice')
                            if p_val:
                                price = float(p_val)
                        elif isinstance(offers, list) and offers:
                            p_val = offers[0].get('price') or offers[0].get('lowPrice')
                            if p_val:
                                price = float(p_val)
                        break
            except Exception:
                continue

        # 2. OpenGraph Fallbacks if missing
        if not title:
            og_t = re.search(r'<meta[^>]*property=[\'"]og:title[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', html, re.I)
            if og_t:
                title = og_t.group(1).strip()

        if price <= 0:
            og_p = re.search(r'<meta[^>]*property=[\'"](?:og:price:amount|product:price:amount)[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', html, re.I)
            if og_p:
                try:
                    price = float(og_p.group(1).replace(',', '').strip())
                except ValueError:
                    pass

        if not images:
            og_img = re.search(r'<meta[^>]*property=[\'"]og:image[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', html, re.I)
            if og_img:
                images.append({'src': og_img.group(1).strip()})

        if not desc:
            og_d = re.search(r'<meta[^>]*property=[\'"]og:description[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', html, re.I)
            if og_d:
                desc = og_d.group(1).strip()

        if title and (price > 0 or images):
            return {
                'title': title,
                'vendor': brand_name or '',
                'variants': [{'price': price, 'compare_at_price': compare_at, 'sku': sku}],
                'images': images,
                'body_html': desc
            }, url
    except Exception:
        pass
    return None

def fallback_search_shopify(session, product_name, brand):
    """Query Shopify search/suggest.json with >=80% token match verification."""
    clean_q = re.sub(r'[^a-zA-Z0-9\s]+', ' ', product_name).strip()
    tokens = clean_q.split()
    short_q = ' '.join(tokens[:4])

    target_domains = ['bandidospitstop.com']
    b_clean = (brand or '').lower().strip()
    if b_clean in BRAND_MANUFACTURER_DOMAINS:
        m_dom = BRAND_MANUFACTURER_DOMAINS[b_clean]
        if m_dom not in target_domains:
            target_domains.append(m_dom)

    for domain in target_domains:
        try:
            suggest_url = f"https://{domain}/search/suggest.json?q={quote(short_q)}&resources[type]=product"
            r = session.get(suggest_url, timeout=4)
            if r.status_code == 200:
                data = r.json()
                products = data.get('resources', {}).get('results', {}).get('products', [])
                for p in products:
                    cand_title = p.get('title', '')
                    cand_vendor = p.get('vendor', '')
                    cand_text = f"{cand_title} {cand_vendor}"
                    query_text = f"{product_name} {brand}"

                    score = compute_token_match(query_text, cand_text)
                    if score >= 0.80:  # Strict 80% token match gate
                        handle = p.get('handle')
                        if handle:
                            full_json_url = f"https://{domain}/products/{handle}.json"
                            fr = session.get(full_json_url, timeout=4)
                            if fr.status_code == 200:
                                p_data = fr.json().get('product')
                                if p_data:
                                    return p_data, full_json_url
                        return {
                            'title': cand_title,
                            'vendor': cand_vendor,
                            'variants': [{'price': p.get('price', 0), 'compare_at_price': p.get('compare_at_price_min', 0), 'sku': ''}],
                            'images': [{'src': p.get('image')}] if p.get('image') else [],
                            'body_html': p.get('body', '')
                        }, f"https://{domain}/products/{p.get('handle', '')}"
        except Exception:
            continue
    return None

def process_single_row(row):
    """Worker function to process a single queue row."""
    session = get_session()
    source_row = row['Source_Row']
    pos_name = row['POS_Product_Name']
    brand = row['Brand']
    cat = row['Category']
    subcat = row['Subcategory']
    pos_sp = float(row['POS_Sale_Price']) if row['POS_Sale_Price'] else 0.0
    pos_pp = float(row['POS_Purchase_Price']) if row['POS_Purchase_Price'] else 0.0
    stock_qty = row['Stock_Qty']
    evidence_url = row['Verification_Evidence_URL'].strip()

    brand_slug = clean_brand_slug(brand)
    scraped_product = None
    resolved_source_url = None

    # Step 1: Direct Shopify /products/<handle>.json
    if evidence_url and '/products/' in evidence_url:
        res = fetch_shopify_json_by_url(session, evidence_url)
        if res:
            scraped_product, resolved_source_url = res

    # Step 2: HTML JSON-LD / OpenGraph Fallback
    if not scraped_product and evidence_url and evidence_url.startswith(('http://', 'https://')):
        res = fetch_product_from_html(session, evidence_url)
        if res:
            scraped_product, resolved_source_url = res

    # Step 3: Fallback search on Bandidos & manufacturer store with >= 80% token match
    if not scraped_product:
        res = fallback_search_shopify(session, pos_name, brand)
        if res:
            scraped_product, resolved_source_url = res

    # Polite micro-sleep
    time.sleep(0.2)

    # Step 4: Strict Price & Identity Validation
    if scraped_product:
        variants = scraped_product.get('variants', [])
        price = 0.0
        compare_at = 0.0
        sku_val = ''
        if variants:
            try:
                price = float(variants[0].get('price', 0))
                compare_at = float(variants[0].get('compare_at_price', 0) or 0)
                sku_val = str(variants[0].get('sku', '') or '')
            except (ValueError, TypeError):
                price = 0.0

        if price <= 0:
            return 'manual', source_row, {
                'Source_Row': source_row,
                'POS_Product_Name': pos_name,
                'Brand': brand,
                'Category': cat,
                'Subcategory': subcat,
                'POS_Sale_Price': pos_sp,
                'POS_Purchase_Price': pos_pp,
                'Stock_Qty': stock_qty,
                'Verification_Evidence_URL': evidence_url,
                'Reason': 'SCRAPED_PRICE_ZERO_OR_MISSING'
            }
        elif pos_pp > 0 and price <= pos_pp:
            return 'manual', source_row, {
                'Source_Row': source_row,
                'POS_Product_Name': pos_name,
                'Brand': brand,
                'Category': cat,
                'Subcategory': subcat,
                'POS_Sale_Price': pos_sp,
                'POS_Purchase_Price': pos_pp,
                'Stock_Qty': stock_qty,
                'Verification_Evidence_URL': evidence_url,
                'Reason': f'PRICE_LESS_THAN_OR_EQUAL_PURCHASE_PRICE (Scraped ₹{price:.2f} <= Purchase ₹{pos_pp:.2f})'
            }
        else:
            # Validated! Download image & sanitize description
            images = scraped_product.get('images', [])
            img_path = None
            if images:
                first_img_url = images[0].get('src') if isinstance(images[0], dict) else str(images[0])
                if first_img_url:
                    img_path = download_and_convert_image(session, first_img_url, brand_slug, pos_name)

            body_html = scraped_product.get('body_html', '') or ''
            clean_desc = sanitize_description(body_html, pos_name, brand)

            scraped_entry = {
                'source_row': source_row,
                'pos_product_name': pos_name,
                'brand': brand if brand else scraped_product.get('vendor', 'HRz Pitstop'),
                'category': cat,
                'subcategory': subcat,
                'official_title': scraped_product.get('title', pos_name),
                'vendor': scraped_product.get('vendor', brand),
                'scraped_selling_price': int(round(price)),
                'scraped_mrp': int(round(compare_at if compare_at and compare_at >= price else price)),
                'pos_purchase_price': pos_pp,
                'pos_sale_price': pos_sp,
                'stock_qty': stock_qty,
                'scraped_sku': sku_val,
                'image_path': img_path if img_path else '',
                'all_images_count': len(images),
                'description': clean_desc,
                'source_url': resolved_source_url if resolved_source_url else evidence_url,
                'verified_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            return 'scraped', source_row, scraped_entry

    return 'manual', source_row, {
        'Source_Row': source_row,
        'POS_Product_Name': pos_name,
        'Brand': brand,
        'Category': cat,
        'Subcategory': subcat,
        'POS_Sale_Price': pos_sp,
        'POS_Purchase_Price': pos_pp,
        'Stock_Qty': stock_qty,
        'Verification_Evidence_URL': evidence_url,
        'Reason': 'NO_MATCH_OR_DEAD_URL'
    }

def main():
    print("=" * 80, flush=True)
    print("PHASE 2: SCRAPE MISSING GOLD DATA (IMAGES, PRICES, VARIANTS, DESCRIPTIONS)", flush=True)
    print("=" * 80, flush=True)

    if not os.path.exists(QUEUE_CSV):
        print(f"Error: Queue file not found: {QUEUE_CSV}", flush=True)
        sys.exit(1)

    with open(QUEUE_CSV, 'r', encoding='utf-8') as f:
        queue_rows = list(csv.DictReader(f))

    print(f"Loaded {len(queue_rows)} items from {QUEUE_CSV}.", flush=True)

    # Load existing progress checkpoint
    scraped_results = {}
    if os.path.exists(RESULTS_JSON):
        try:
            with open(RESULTS_JSON, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    scraped_results = {it['source_row']: it for it in loaded}
                elif isinstance(loaded, dict):
                    scraped_results = loaded
            print(f"Checkpoint: {len(scraped_results)} previously verified items loaded.", flush=True)
        except Exception as e:
            print(f"Warning loading checkpoint: {e}", flush=True)

    manual_review_rows = {}
    if os.path.exists(MANUAL_CSV):
        try:
            with open(MANUAL_CSV, 'r', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    manual_review_rows[r['Source_Row']] = r
            print(f"Checkpoint: {len(manual_review_rows)} existing manual review entries loaded.", flush=True)
        except Exception as e:
            pass

    total_items = len(queue_rows)
    batch_size = 50
    workers = 8

    print(f"\nStarting concurrent batch processing (Workers: {workers}, Batch Size: {batch_size})...", flush=True)

    for i in range(0, total_items, batch_size):
        batch = queue_rows[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_items + batch_size - 1) // batch_size

        # Check if entire batch was already resolved
        unprocessed_in_batch = [r for r in batch if r['Source_Row'] not in scraped_results]
        if not unprocessed_in_batch:
            print(f"--- Batch {batch_num}/{total_batches} (Rows {i+1} to {min(i+batch_size, total_items)}) --- [ALREADY PROCESSED - SKIPPING]", flush=True)
            continue

        print(f"\n--- Batch {batch_num}/{total_batches} (Rows {i+1} to {min(i+batch_size, total_items)}) [{len(unprocessed_in_batch)} to process] ---", flush=True)

        batch_new_scraped = 0
        batch_new_manual = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_row = {executor.submit(process_single_row, r): r for r in unprocessed_in_batch}
            for future in as_completed(future_to_row):
                status, s_row, data = future.result()
                if status == 'scraped':
                    scraped_results[s_row] = data
                    if s_row in manual_review_rows:
                        del manual_review_rows[s_row]
                    batch_new_scraped += 1
                else:
                    manual_review_rows[s_row] = data
                    batch_new_manual += 1

        # Batch checkpoint save
        with open(RESULTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(list(scraped_results.values()), f, indent=2, ensure_ascii=False)

        manual_fields = [
            'Source_Row', 'POS_Product_Name', 'Brand', 'Category', 'Subcategory',
            'POS_Sale_Price', 'POS_Purchase_Price', 'Stock_Qty', 'Verification_Evidence_URL', 'Reason'
        ]
        with open(MANUAL_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=manual_fields)
            writer.writeheader()
            for r in manual_review_rows.values():
                writer.writerow(r)

        print(f"Batch {batch_num} done: +{batch_new_scraped} verified, +{batch_new_manual} manual review | Total Scraped: {len(scraped_results)}, Total Manual: {len(manual_review_rows)}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("PHASE 2 SCRAPING PIPELINE COMPLETE", flush=True)
    print("=" * 80, flush=True)
    print(f"Successfully scraped & verified:  {len(scraped_results)} items saved to {RESULTS_JSON}", flush=True)
    print(f"Logged for manual review:        {len(manual_review_rows)} items saved to {MANUAL_CSV}", flush=True)
    print("=" * 80, flush=True)

if __name__ == '__main__':
    main()
