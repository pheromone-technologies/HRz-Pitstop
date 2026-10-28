#!/usr/bin/env python3
"""
HRz Pitstop: Multi-Angle Product Gallery & Color-Separated Pipeline
Repo: E:\\coad\\hrx website 2

Pipeline Rules:
1. Strict Color Separation:
   - Products with specific colors (e.g. White/Blue vs White/Red or Matt Black vs Gloss Red)
     must ONLY receive images of that specific colorway.
   - Images of different color variants must NEVER be mixed into the same product gallery.
2. Multiple Camera Angles:
   - For each product and colorway, extracts up to 3-4 clean product photography angles
     (Front, 45-degree, Side Profile, Rear/Detail view).
   - Filters out non-product junk (size charts, measurement diagrams, banners, GIFs).
3. Uniform Processing on EVERY Angle:
   - Background removed via rembg (u2netp) -> eliminates background watermarks & artifacts.
   - Composited onto pure clean white canvas (255, 255, 255).
   - Official HRZ logo stamped in bottom-right corner.
   - WebP compressed (quality 85) at images_processed/catalog/<brand>/<product>_<angle>.webp.
4. Data Sync:
   - Updates Verified_Products_FINAL-1.xlsx with 'Product Image Filename / URL' and 'Gallery Images'.
   - Syncs into data/products.json with variant-aware color galleries.
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
CHECKPOINT_FILE = os.path.join(BASE_DIR, "tools", "output", "multi_angle_checkpoint.json")
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

_local = threading.local()

def get_thread_resources():
    if not hasattr(_local, 'rembg_session'):
        _local.rembg_session = new_session('u2netp')
    if not hasattr(_local, 'http_session'):
        s = requests.Session()
        s.headers.update(HEADERS)
        _local.http_session = s
    return _local.http_session, _local.rembg_session

if not os.path.exists(LOGO_FILE):
    raise FileNotFoundError(f"HRZ Logo not found at {LOGO_FILE}")
HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

JUNK_KEYWORDS = {'chart', 'size', 'sizing', 'table', 'dimension', 'measurement', 'diagram', 'banner', 'badge', 'logo', 'warranty'}

COLOR_KEYWORDS = {
    'black': ['black', 'blk', 'nero'],
    'white': ['white', 'wht', 'bianco'],
    'red': ['red', 'rosso'],
    'blue': ['blue', 'blu', 'azzurro'],
    'green': ['green', 'grn', 'verde'],
    'yellow': ['yellow', 'yel', 'giallo', 'flouriscent'],
    'orange': ['orange', 'orng', 'arancio'],
    'grey': ['grey', 'gray', 'titanium'],
    'silver': ['silver', 'slv'],
    'gold': ['gold', 'gld'],
    'neon': ['neon', 'hi-viz', 'hiviz']
}

def sanitize_slug(name):
    if not name:
        return 'unbranded'
    clean = re.sub(r'[^a-zA-Z0-9_-]+', '_', str(name)).strip('_')
    return clean[:55].lower()

def extract_color_tokens(name_or_color):
    tokens = set()
    txt = str(name_or_color).lower()
    for col_key, aliases in COLOR_KEYWORDS.items():
        if any(re.search(r'\b' + re.escape(a) + r'\b', txt) for a in aliases):
            tokens.add(col_key)
    return tokens

def is_image_matching_color(img_src, img_alt, target_colors):
    """Ensure image belongs to the product's colorway, rejecting competing colors."""
    if not target_colors:
        return True # Universal or single-color part
        
    combined_txt = f"{img_src} {img_alt}".lower()
    img_colors = extract_color_tokens(combined_txt)
    
    # If image explicitly names colors, check if it conflicts
    if img_colors:
        # If it has a color NOT in target_colors, and doesn't match target_colors, reject it
        competing = img_colors.difference(target_colors)
        if competing and not img_colors.intersection(target_colors):
            return False
            
    return True

def fetch_clean_angles_from_shopify(session, json_url, target_colors):
    """Extract up to 4 clean camera angles from Shopify JSON."""
    try:
        r = session.get(json_url, timeout=5)
        if r.status_code != 200:
            return []
            
        data = r.json().get('product', {})
        images = data.get('images', [])
        variants = data.get('variants', [])
        
        # Check if variants have specific image_ids
        color_matched_img_ids = set()
        if target_colors and variants:
            for v in variants:
                v_title = (v.get('title') or '').lower()
                v_colors = extract_color_tokens(v_title)
                if v_colors and v_colors.intersection(target_colors):
                    if v.get('image_id'):
                        color_matched_img_ids.add(v.get('image_id'))
                        
        valid_angles = []
        for im in images:
            src = im.get('src') if isinstance(im, dict) else str(im)
            if not src: continue
            src_lower = src.lower()
            
            # Skip non-photo media
            if src_lower.endswith('.gif') or '.gif?' in src_lower or src_lower.endswith('.svg'):
                continue
                
            alt = (im.get('alt') or '').lower() if isinstance(im, dict) else ''
            # Skip size charts and diagrams
            if any(w in src_lower for w in JUNK_KEYWORDS) or any(w in alt for w in JUNK_KEYWORDS):
                continue
                
            # If color-specific image IDs found, prioritize them
            im_id = im.get('id') if isinstance(im, dict) else None
            if color_matched_img_ids and im_id:
                if im_id not in color_matched_img_ids:
                    continue
            else:
                # Color consistency check on filename / alt
                if not is_image_matching_color(src, alt, target_colors):
                    continue
                    
            clean_url = re.sub(r'\?.*$', '', src)
            if clean_url not in valid_angles:
                valid_angles.append(clean_url)
                if len(valid_angles) >= 4:
                    break
                    
        return valid_angles
    except Exception:
        return []

def process_angle_image(http_session, rembg_session, img_url, target_rel):
    """Download, remove background, place on white canvas, stamp logo, compress to WebP."""
    target_abs = os.path.join(BASE_DIR, target_rel.replace('/', os.sep))
    if os.path.exists(target_abs) and os.path.getsize(target_abs) > 2048:
        return target_rel
        
    try:
        r = http_session.get(img_url, timeout=10)
        if r.status_code != 200 or len(r.content) < 1024:
            return None
            
        raw = Image.open(io.BytesIO(r.content)).convert('RGBA')
        raw.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        
        nobg = remove(raw, session=rembg_session)
        
        w, h = nobg.size
        white_bg = Image.new('RGBA', (w, h), (255, 255, 255, 255))
        white_bg.alpha_composite(nobg)
        
        scale_factor = 0.15
        padding = max(15, int(w * 0.02))
        
        wm_w = int(w * scale_factor)
        wm_ratio = wm_w / float(HRZ_LOGO.width)
        wm_h = int(HRZ_LOGO.height * wm_ratio)
        resized_logo = HRZ_LOGO.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
        
        x = w - wm_w - padding
        y = h - wm_h - padding
        white_bg.alpha_composite(resized_logo, dest=(x, y))
        
        os.makedirs(os.path.dirname(target_abs), exist_ok=True)
        final_rgb = white_bg.convert('RGB')
        final_rgb.save(target_abs, 'WEBP', quality=85)
        
        if os.path.exists(target_abs) and os.path.getsize(target_abs) > 1024:
            return target_rel
    except Exception:
        pass
    return None

def process_product_gallery(row_data, existing_primary_map):
    row_idx = row_data['row_idx']
    pname = (row_data.get('Product Name') or '').strip()
    brand = (row_data.get('Brand') or 'Unbranded').strip()
    color_val = (row_data.get('Colour') or '').strip()
    evidence_url = (row_data.get('Evidence Link') or row_data.get('Verification Evidence') or '').strip()
    
    brand_slug = sanitize_slug(brand)
    pname_slug = sanitize_slug(pname)
    if not pname_slug:
        pname_slug = f"prod_{row_idx}"
        
    primary_rel = existing_primary_map.get(str(row_idx)) or f"images_processed/catalog/{brand_slug}/{pname_slug}.webp"
    
    # Extract target colors for strict color separation
    target_colors = extract_color_tokens(f"{pname} {color_val}")
    
    http_session, rembg_session = get_thread_resources()
    angle_urls = []
    
    # Check Shopify JSON for multiple angles
    if '/products/' in evidence_url:
        m = re.search(r'/products/([^/?#]+)', evidence_url)
        if m:
            handle = m.group(1)
            parsed = urllib.parse.urlparse(evidence_url)
            json_url = f"{parsed.scheme}://{parsed.netloc}/products/{handle}.json"
            angle_urls = fetch_clean_angles_from_shopify(http_session, json_url, target_colors)
            
    gallery_paths = []
    if angle_urls:
        for idx, u in enumerate(angle_urls):
            angle_target_rel = f"images_processed/catalog/{brand_slug}/{pname_slug}_{idx+1}.webp"
            processed_rel = process_angle_image(http_session, rembg_session, u, angle_target_rel)
            if processed_rel:
                gallery_paths.append(processed_rel)
                
    # If no secondary angles were available from URL or not multi-angle, use the primary image
    if not gallery_paths:
        primary_abs = os.path.join(BASE_DIR, primary_rel.replace('/', os.sep))
        if os.path.exists(primary_abs):
            gallery_paths.append(primary_rel)
            
    return {
        'row_idx': row_idx,
        'product_name': pname,
        'brand': brand,
        'primary_image': gallery_paths[0] if gallery_paths else primary_rel,
        'gallery': gallery_paths,
        'angles_count': len(gallery_paths)
    }

def main():
    print("=" * 80)
    print("HRZ PITSTOP: MULTI-ANGLE GALLERY & STRICT COLOR-SEPARATED PIPELINE")
    print("=" * 80)
    
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    
    products = []
    for r_idx in range(2, ws.max_row + 1):
        row_vals = [ws.cell(r_idx, c_idx).value for c_idx in range(1, len(headers) + 1)]
        row_dict = dict(zip(headers, row_vals))
        row_dict['row_idx'] = r_idx
        products.append(row_dict)
        
    print(f"Loaded {len(products)} products from {EXCEL_FILE}.")
    
    # Load primary image paths from previous checkpoint
    existing_primary = {}
    prev_chk_file = os.path.join(BASE_DIR, "tools", "output", "verified_images_checkpoint.json")
    if os.path.exists(prev_chk_file):
        with open(prev_chk_file, 'r', encoding='utf-8') as f:
            prev_chk = json.load(f)
            for k, v in prev_chk.items():
                if v.get('image_path'):
                    existing_primary[k] = v['image_path']
                    
    # Checkpoint for multi-angle
    checkpoint = {}
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"Resuming multi-angle checkpoint: {len(checkpoint)} products already processed.")
        except Exception:
            checkpoint = {}
            
    pending = [p for p in products if str(p['row_idx']) not in checkpoint or not checkpoint[str(p['row_idx'])].get('gallery')]
    print(f"Products to process in this multi-angle pass: {len(pending)}")
    
    workers = 4
    start_time = time.time()
    done_count = len(products) - len(pending)
    multi_angle_count = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_product_gallery, p, existing_primary): p
            for p in pending
        }
        
        for future in as_completed(futures):
            res = future.result()
            r_str = str(res['row_idx'])
            checkpoint[r_str] = res
            if res.get('angles_count', 0) > 1:
                multi_angle_count += 1
                
            done_count += 1
            if done_count % 25 == 0 or done_count == len(products):
                elapsed = time.time() - start_time
                rate = (done_count - (len(products) - len(pending))) / elapsed if elapsed > 0 else 0
                remaining = (len(products) - done_count) / rate if rate > 0 else 0
                print(f"Multi-Angle Progress: [{done_count}/{len(products)}] | Products with Multi-Angles: {multi_angle_count} | Rate: {rate:.1f} it/s | Est: {remaining/60:.1f}m", flush=True)
                
                with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint, f, indent=2)

    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2)

    print("\nMulti-Angle Extraction Complete!")
    total_angles_generated = sum(len(v.get('gallery', [])) for v in checkpoint.values())
    print(f"Total processed products: {len(checkpoint)}")
    print(f"Total clean, branded WebP angle images across all products: {total_angles_generated}")

    # Update Verified_Products_FINAL-1.xlsx with Gallery Images column
    print("\nWriting gallery images to Verified_Products_FINAL-1.xlsx...")
    wb_write = openpyxl.load_workbook(EXCEL_FILE)
    ws_write = wb_write.active
    col_headers = [ws_write.cell(1, c).value for c in range(1, ws_write.max_column + 1)]
    
    if 'Gallery Images' in col_headers:
        gallery_col_idx = col_headers.index('Gallery Images') + 1
    else:
        gallery_col_idx = ws_write.max_column + 1
        ws_write.cell(1, gallery_col_idx, 'Gallery Images')
        
    img_col_idx = col_headers.index('Product Image Filename / URL') + 1 if 'Product Image Filename / URL' in col_headers else gallery_col_idx - 1
    
    for r_idx in range(2, ws_write.max_row + 1):
        r_str = str(r_idx)
        if r_str in checkpoint:
            entry = checkpoint[r_str]
            gal = entry.get('gallery', [])
            if gal:
                ws_write.cell(r_idx, img_col_idx, gal[0])
                ws_write.cell(r_idx, gallery_col_idx, ", ".join(gal))
                
    wb_write.save(EXCEL_FILE)
    print(f"Successfully saved {EXCEL_FILE} with multi-angle Gallery Images populated!")

    # Sync to data/products.json with variant-aware color separation
    print("\nSyncing multi-angle galleries to data/products.json...")
    try:
        with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
            site_products = json.load(f)
            
        p_by_name = {p['name'].strip().lower(): p for p in site_products if p.get('name')}
        
        synced = 0
        for entry in checkpoint.values():
            pname = entry.get('product_name', '').strip().lower()
            gal = entry.get('gallery', [])
            if not gal: continue
            
            target = p_by_name.get(pname)
            if target:
                target['image'] = gal[0]
                target['gallery'] = gal
                synced += 1
                
        with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(site_products, f, indent=2)
        print(f"Synced {synced} storefront products with full multi-angle galleries in products.json!")
    except Exception as e:
        print(f"Warning syncing products.json: {e}")
        
    print("=" * 80)

if __name__ == '__main__':
    main()
