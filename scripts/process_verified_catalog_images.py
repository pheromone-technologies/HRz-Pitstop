#!/usr/bin/env python3
"""
HRz Pitstop: Verified Catalog Images Processing Pipeline
Repo: E:\\coad\\hrx website 2

Pipeline Specification:
1. Input: E:\\coad\\hrx website 2\\Verified_Products_FINAL-1.xlsx (all 1,806 verified products).
2. For each product:
   a. Source raw image from:
      - Local disk cache (images_processed/scraped/ and images/) via exact / fuzzy key matching
      - Direct Shopify .json API (from Evidence Link / Verification Evidence)
      - OpenGraph / JSON-LD / HTML image extraction from verification URLs
      - Targeted search fallback if URL is broken or generic
   b. Background Removal using rembg (u2netp model session) -> strips backgrounds, competitor watermarks & artifacts.
   c. Composite isolated product onto a pristine, pure white canvas (255, 255, 255).
   d. Stamp official HRZ logo (from E:\\coad\\tools for hrz\\image logo editor) into the bottom-right corner.
   e. Compress to optimized WebP format (quality 85) at images_processed/catalog/<brand_slug>/<product_slug>.webp.
3. Checkpoint & Progress Tracking:
   - Saves intermediate progress into tools/output/verified_images_checkpoint.json.
   - Resumes seamlessly if interrupted.
4. Output Sync:
   - Updates Verified_Products_FINAL-1.xlsx with 'Product Image Filename / URL'.
   - Syncs into data/products.json for storefront rendering.
"""

import os
import sys
import io
import re
import json
import time
import urllib.parse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from PIL import Image
import openpyxl
from rembg import remove, new_session

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
EXCEL_FILE = os.path.join(BASE_DIR, "Verified_Products_FINAL-1.xlsx")
LOGO_FILE = r"E:\coad\tools for hrz\image logo editor\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"
OUTPUT_DIR = os.path.join(BASE_DIR, "images_processed", "catalog")
CHECKPOINT_FILE = os.path.join(BASE_DIR, "tools", "output", "verified_images_checkpoint.json")
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)

# Common HTTP Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Thread-local storage for requests session and rembg session
_local = threading.local()

def get_thread_resources():
    if not hasattr(_local, 'rembg_session'):
        _local.rembg_session = new_session('u2netp')
    if not hasattr(_local, 'http_session'):
        s = requests.Session()
        s.headers.update(HEADERS)
        _local.http_session = s
    return _local.http_session, _local.rembg_session

# Preload HRZ Logo
if not os.path.exists(LOGO_FILE):
    raise FileNotFoundError(f"HRZ Logo not found at {LOGO_FILE}")
HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

def sanitize_slug(name):
    if not name:
        return 'unbranded'
    clean = re.sub(r'[^a-zA-Z0-9_-]+', '_', str(name)).strip('_')
    return clean[:55].lower()

def extract_image_url(session, page_url):
    """Extract direct high-res image URL from verification page."""
    if not page_url or not str(page_url).startswith(('http://', 'https://')):
        return None
        
    try:
        parsed = urllib.parse.urlparse(page_url)
        path = parsed.path
        
        # 1. Direct Image URL
        if path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
            return page_url
            
        # 2. Shopify Fast-Path (/products/<handle>)
        if '/products/' in path:
            m = re.search(r'/products/([^/?#]+)', path)
            if m:
                handle = m.group(1)
                json_url = f"{parsed.scheme}://{parsed.netloc}/products/{handle}.json"
                try:
                    r = session.get(json_url, timeout=5)
                    if r.status_code == 200:
                        prod = r.json().get('product', {})
                        images = prod.get('images', [])
                        if images:
                            src = images[0].get('src') if isinstance(images[0], dict) else str(images[0])
                            clean_src = re.sub(r'\?.*$', '', src)
                            return clean_src
                except Exception:
                    pass
                    
        # 3. HTML parsing fallback (OpenGraph, Twitter, JSON-LD, CDN patterns)
        r = session.get(page_url, timeout=6)
        if r.status_code == 200 and r.text:
            html = r.text
            
            # OpenGraph
            m = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
            if not m:
                m = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html, re.I)
            if m:
                img_url = m.group(1).strip()
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                return img_url
                
            # JSON-LD schema
            m_ld = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', html, re.I)
            for block in m_ld:
                try:
                    data = json.loads(block.strip())
                    items = data if isinstance(data, list) else [data]
                    for it in items:
                        if isinstance(it, dict) and 'image' in it:
                            img = it['image']
                            if isinstance(img, list) and img:
                                return img[0] if isinstance(img[0], str) else img[0].get('url')
                            elif isinstance(img, str):
                                return img
                            elif isinstance(img, dict):
                                return img.get('url')
                except Exception:
                    pass
                    
            # Specific domain patterns
            m_im = re.search(r'https://[0-9]+\.imimg\.com/[^"\'>\s]+', html)
            if m_im:
                return m_im.group(0)
                
            m_mog = re.search(r'https://cdn\.moglix\.com/p/[a-zA-Z0-9_-]+\.(?:jpg|png|jpeg)', html)
            if m_mog:
                return m_mog.group(0)
                
            m_fk = re.search(r'https://rukminim[0-9]*\.flixcart\.com/image/[^"\'>\s]+', html)
            if m_fk:
                return m_fk.group(0)

    except Exception:
        pass
    return None

def process_single_product(row_data, disk_index):
    """Pipeline processor for one product row."""
    row_idx = row_data['row_idx']
    pname = (row_data.get('Product Name') or '').strip()
    brand = (row_data.get('Brand') or 'Unbranded').strip()
    sku = (row_data.get('SKU') or '').strip()
    evidence_url = (row_data.get('Evidence Link') or row_data.get('Verification Evidence') or '').strip()
    
    brand_slug = sanitize_slug(brand)
    pname_slug = sanitize_slug(pname)
    if not pname_slug:
        pname_slug = f"prod_{row_idx}"
        
    target_rel = f"images_processed/catalog/{brand_slug}/{pname_slug}.webp"
    target_abs = os.path.join(BASE_DIR, target_rel.replace('/', os.sep))
    
    # 0. Check if already processed
    if os.path.exists(target_abs) and os.path.getsize(target_abs) > 2048:
        return {
            'row_idx': row_idx,
            'product_name': pname,
            'image_path': target_rel,
            'status': 'CACHED',
            'error': None
        }
        
    http_session, rembg_session = get_thread_resources()
    raw_img = None
    source_used = None
    
    # Strategy 1: Check existing local disk index by normalized product name or SKU
    pname_clean = re.sub(r'[^a-z0-9]', '', pname.lower())
    sku_clean = re.sub(r'[^a-z0-9]', '', sku.lower())
    
    # Check exact match
    match_path = None
    if pname_clean in disk_index:
        match_path = disk_index[pname_clean]
    elif sku_clean and sku_clean != 'missingsku' and sku_clean in disk_index:
        match_path = disk_index[sku_clean]
    elif len(pname_clean) >= 15:
        # Check prefix match in disk index
        prefix = pname_clean[:22]
        for dk, dpath in disk_index.items():
            if dk.startswith(prefix) or prefix in dk:
                match_path = dpath
                break
                
    if match_path and os.path.exists(match_path) and os.path.getsize(match_path) > 1024:
        try:
            raw_img = Image.open(match_path).convert('RGBA')
            source_used = f"local_disk:{os.path.basename(match_path)}"
        except Exception:
            raw_img = None
                
    # Strategy 2: Download from verification evidence URL
    if raw_img is None and evidence_url:
        direct_img_url = extract_image_url(http_session, evidence_url)
        if direct_img_url:
            try:
                r = http_session.get(direct_img_url, timeout=10)
                if r.status_code == 200 and len(r.content) > 1024:
                    raw_img = Image.open(io.BytesIO(r.content)).convert('RGBA')
                    source_used = f"url:{direct_img_url}"
            except Exception:
                raw_img = None

    # Strategy 3: Fallback suggest search if URL failed or missing
    if raw_img is None:
        try:
            tokens = re.sub(r'[^a-zA-Z0-9\s]+', ' ', pname).split()[:4]
            short_q = ' '.join(tokens)
            suggest_url = f"https://bandidospitstop.com/search/suggest.json?q={urllib.parse.quote(short_q)}&resources[type]=product"
            sr = http_session.get(suggest_url, timeout=5)
            if sr.status_code == 200:
                sdata = sr.json().get('resources', {}).get('results', {}).get('products', [])
                if sdata and sdata[0].get('image'):
                    fb_img_url = sdata[0]['image']
                    if fb_img_url.startswith('//'):
                        fb_img_url = 'https:' + fb_img_url
                    fr = http_session.get(fb_img_url, timeout=8)
                    if fr.status_code == 200 and len(fr.content) > 1024:
                        raw_img = Image.open(io.BytesIO(fr.content)).convert('RGBA')
                        source_used = f"suggest_search:{fb_img_url}"
        except Exception:
            pass
            
    if raw_img is None:
        return {
            'row_idx': row_idx,
            'product_name': pname,
            'image_path': '',
            'status': 'NO_IMAGE_FOUND',
            'error': f'Failed to obtain raw image from {evidence_url}'
        }

    # =========================================================================
    # CORE PIPELINE: REMBG -> CLEAN WHITE BG -> HRZ LOGO -> COMPRESSED WEBP
    # =========================================================================
    try:
        # Resize thumbnail before rembg if too large to ensure speed and preserve aspect ratio
        raw_img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        
        # 1. Background removal using rembg
        nobg = remove(raw_img, session=rembg_session)
        
        # 2. Composite onto clean pure white background
        w, h = nobg.size
        white_bg = Image.new('RGBA', (w, h), (255, 255, 255, 255))
        white_bg.alpha_composite(nobg)
        
        # 3. Add HRZ logo in the bottom-right corner
        scale_factor = 0.15
        padding = max(15, int(w * 0.02))
        
        wm_w = int(w * scale_factor)
        wm_ratio = wm_w / float(HRZ_LOGO.width)
        wm_h = int(HRZ_LOGO.height * wm_ratio)
        resized_logo = HRZ_LOGO.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
        
        x = w - wm_w - padding
        y = h - wm_h - padding
        white_bg.alpha_composite(resized_logo, dest=(x, y))
        
        # 4. Convert to RGB and compress as WebP
        os.makedirs(os.path.dirname(target_abs), exist_ok=True)
        final_rgb = white_bg.convert('RGB')
        final_rgb.save(target_abs, 'WEBP', quality=85)
        
        if os.path.exists(target_abs) and os.path.getsize(target_abs) > 1024:
            return {
                'row_idx': row_idx,
                'product_name': pname,
                'image_path': target_rel,
                'status': 'PROCESSED',
                'source': source_used,
                'size_bytes': os.path.getsize(target_abs),
                'error': None
            }
        else:
            return {
                'row_idx': row_idx,
                'product_name': pname,
                'image_path': '',
                'status': 'SAVE_FAILED',
                'error': 'Saved file missing or empty'
            }
            
    except Exception as e:
        return {
            'row_idx': row_idx,
            'product_name': pname,
            'image_path': '',
            'status': 'PIPELINE_ERROR',
            'error': str(e)
        }

def sync_storefront_products(checkpoint):
    """Sync newly processed image paths to data/products.json."""
    if not os.path.exists(PRODUCTS_JSON):
        return
    try:
        with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
            products = json.load(f)
            
        p_by_name = {}
        for p in products:
            p_by_name[p['name'].strip().lower()] = p
            
        updated = 0
        for entry in checkpoint.values():
            pname = entry.get('product_name', '').strip().lower()
            ipath = entry.get('image_path')
            if pname and ipath and pname in p_by_name:
                p_by_name[pname]['image'] = ipath
                p_by_name[pname]['gallery'] = [ipath]
                updated += 1
                
        with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2)
        print(f"Sync complete: Updated {updated} products in data/products.json with clean branded images!")
    except Exception as e:
        print(f"Warning syncing to products.json: {e}")

def main():
    print("=" * 80)
    print("HRZ PITSTOP: VERIFIED PRODUCTS IMAGE PROCESSING PIPELINE")
    print("=" * 80)
    print(f"Reading verified master: {EXCEL_FILE}")
    
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    
    products = []
    for r_idx in range(2, ws.max_row + 1):
        row_vals = [ws.cell(r_idx, c_idx).value for c_idx in range(1, len(headers) + 1)]
        row_dict = dict(zip(headers, row_vals))
        row_dict['row_idx'] = r_idx
        products.append(row_dict)
        
    print(f"Total verified products loaded: {len(products)}")
    
    # Build local disk index across scraped cache and images
    print("Building local disk image index...")
    disk_index = {}
    scan_dirs = [
        os.path.join(BASE_DIR, 'images_processed', 'scraped'),
        os.path.join(BASE_DIR, 'images')
    ]
    for sdir in scan_dirs:
        if os.path.exists(sdir):
            for root, _, files in os.walk(sdir):
                for f in files:
                    if f.lower().endswith(('.webp', '.jpg', '.png', '.jpeg')):
                        k = re.sub(r'[^a-z0-9]', '', os.path.splitext(f)[0].lower())
                        if k and k not in disk_index:
                            disk_index[k] = os.path.join(root, f)
    print(f"Indexed {len(disk_index)} local product images for fast resolution.")

    # Load checkpoint
    checkpoint = {}
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"Checkpoint loaded: {len(checkpoint)} products already tracked.")
        except Exception:
            checkpoint = {}
            
    # Filter products that still need processing
    pending = []
    for p in products:
        r_str = str(p['row_idx'])
        if r_str in checkpoint and checkpoint[r_str].get('image_path'):
            chk_abs = os.path.join(BASE_DIR, checkpoint[r_str]['image_path'].replace('/', os.sep))
            if os.path.exists(chk_abs) and os.path.getsize(chk_abs) > 2048:
                continue
        pending.append(p)
        
    print(f"Products to process in this run: {len(pending)} (Already cached: {len(products) - len(pending)})")
    
    # Process concurrently with ThreadPoolExecutor
    workers = 4
    start_time = time.time()
    processed_count = len(products) - len(pending)
    new_success = 0
    new_failed = 0
    
    print(f"\nStarting pipeline execution with {workers} concurrent workers...", flush=True)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_row = {
            executor.submit(process_single_product, p, disk_index): p
            for p in pending
        }
        
        for future in as_completed(future_to_row):
            res = future.result()
            r_str = str(res['row_idx'])
            checkpoint[r_str] = res
            
            if res.get('image_path'):
                new_success += 1
            else:
                new_failed += 1
                
            total_done = processed_count + new_success + new_failed
            if (new_success + new_failed) % 20 == 0 or total_done == len(products):
                elapsed = time.time() - start_time
                rate = (new_success + new_failed) / elapsed if elapsed > 0 else 0
                remaining = (len(pending) - (new_success + new_failed)) / rate if rate > 0 else 0
                print(f"Progress: [{total_done}/{len(products)}] (New Success: {new_success}, Failed: {new_failed}) | {rate:.1f} items/s | Est. Remaining: {remaining/60:.1f}m", flush=True)
                
                # Periodic checkpoint flush
                with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint, f, indent=2)

    # Final checkpoint save
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2)
        
    print(f"\nProcessing Complete in {time.time() - start_time:.1f}s.")
    print(f"Total items in checkpoint: {len(checkpoint)}")
    total_valid_images = sum(1 for v in checkpoint.values() if v.get('image_path'))
    print(f"Total successfully generated clean branded images: {total_valid_images} / {len(products)}")

    # Update Verified_Products_FINAL-1.xlsx with Product Image Filename / URL
    print("\nUpdating Verified_Products_FINAL-1.xlsx with final image paths...")
    wb_write = openpyxl.load_workbook(EXCEL_FILE)
    ws_write = wb_write.active
    
    # Find or append Product Image Filename / URL column
    col_headers = [ws_write.cell(1, c).value for c in range(1, ws_write.max_column + 1)]
    if 'Product Image Filename / URL' in col_headers:
        img_col_idx = col_headers.index('Product Image Filename / URL') + 1
    else:
        img_col_idx = ws_write.max_column + 1
        ws_write.cell(1, img_col_idx, 'Product Image Filename / URL')
        
    updated_rows = 0
    for r_idx in range(2, ws_write.max_row + 1):
        r_str = str(r_idx)
        if r_str in checkpoint and checkpoint[r_str].get('image_path'):
            ws_write.cell(r_idx, img_col_idx, checkpoint[r_str]['image_path'])
            updated_rows += 1
            
    wb_write.save(EXCEL_FILE)
    print(f"Successfully saved {EXCEL_FILE} with {updated_rows} image paths updated!")
    
    # Sync to data/products.json
    sync_storefront_products(checkpoint)
    print("=" * 80)

if __name__ == '__main__':
    main()
