#!/usr/bin/env python3
"""
HRz Pitstop: Recovery Pass for Failed Verified Products Images
Repo: E:\\coad\\hrx website 2

1. Scans tools/output/verified_images_checkpoint.json for items with missing image_path.
2. Strategy A: Local Catalog & Scraped Image Token Matching:
   - Matches words in Product Name against already processed catalog images or scraped images.
   - For example: 'CARBONADO TURTL BLACK THIGH BAG 5L' matches 'carbonado_turtle_black_hard_shell_thigh_bag_5_litres_ca.webp'.
3. Strategy B: DDGS / Direct Image Search fallback:
   - Queries product name on image search, downloads raw photo, passes through:
     rembg -> pure white bg -> HRZ logo bottom-right -> WebP compression.
4. Updates checkpoint, updates Verified_Products_FINAL-1.xlsx, and syncs data/products.json.
"""

import os
import sys
import io
import re
import json
import time
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

session_p = new_session('u2netp')
HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

def sanitize_slug(name):
    if not name:
        return 'unbranded'
    clean = re.sub(r'[^a-zA-Z0-9_-]+', '_', str(name)).strip('_')
    return clean[:55].lower()

def process_and_save_image(raw_img, target_rel):
    target_abs = os.path.join(BASE_DIR, target_rel.replace('/', os.sep))
    os.makedirs(os.path.dirname(target_abs), exist_ok=True)
    
    raw_img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
    nobg = remove(raw_img, session=session_p)
    
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
    
    final_rgb = white_bg.convert('RGB')
    final_rgb.save(target_abs, 'WEBP', quality=85)
    return os.path.exists(target_abs) and os.path.getsize(target_abs) > 1024

def search_ddg_image(query):
    try:
        url = "https://html.duckduckgo.com/html/"
        r = requests.post(url, data={'q': query + ' motorcycle gear'}, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            # find external image links or shopify/indiamart links
            img_urls = re.findall(r'//[^"\'>\s]+\.(?:jpg|jpeg|png|webp)', r.text)
            for iu in img_urls:
                if 'duckduckgo' not in iu:
                    return 'https:' + iu if iu.startswith('//') else iu
    except Exception:
        pass
    return None

def main():
    print("=" * 80)
    print("HRZ PITSTOP: FAILED IMAGES RECOVERY PASS")
    print("=" * 80)
    
    if not os.path.exists(CHECKPOINT_FILE):
        print("Checkpoint file not found.")
        return
        
    with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)
        
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    
    row_map = {}
    for r_idx in range(2, ws.max_row + 1):
        row_vals = [ws.cell(r_idx, c_idx).value for c_idx in range(1, len(headers) + 1)]
        row_map[str(r_idx)] = dict(zip(headers, row_vals))
        
    # Index all already-processed catalog images
    catalog_imgs = []
    for root, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            if f.endswith('.webp'):
                f_words = set(re.sub(r'[^a-z0-9]', ' ', os.path.splitext(f)[0].lower()).split())
                rel_path = os.path.relpath(os.path.join(root, f), BASE_DIR).replace('\\', '/')
                catalog_imgs.append((f_words, rel_path, os.path.join(root, f)))
                
    print(f"Indexed {len(catalog_imgs)} existing clean catalog images for recovery reuse.")
    
    failed_keys = [k for k, v in checkpoint.items() if not v.get('image_path')]
    print(f"Total failed items to recover: {len(failed_keys)}")
    
    recovered = 0
    for k in failed_keys:
        p_data = row_map.get(k, {})
        pname = p_data.get('Product Name') or ''
        brand = p_data.get('Brand') or 'unbranded'
        if not pname: continue
        
        brand_slug = sanitize_slug(brand)
        pname_slug = sanitize_slug(pname)
        target_rel = f"images_processed/catalog/{brand_slug}/{pname_slug}.webp"
        
        # 1. Try Token Match against catalog images
        p_words = set(re.sub(r'[^a-z0-9]', ' ', pname.lower()).split())
        best_match = None
        max_overlap = 0
        for f_words, rel_path, abs_path in catalog_imgs:
            overlap = len(p_words.intersection(f_words))
            if overlap > max_overlap:
                max_overlap = overlap
                best_match = rel_path
                
        # If strong overlap (e.g. >= 60% of words or >= 3 words matching)
        if best_match and (max_overlap >= 3 or max_overlap >= len(p_words) * 0.6):
            checkpoint[k]['image_path'] = best_match
            checkpoint[k]['status'] = 'RECOVERED_CATALOG_MATCH'
            checkpoint[k]['error'] = None
            recovered += 1
            print(f"Recovered [{k}]: {pname} -> Matched: {best_match}")
            continue
            
        # 2. Try Web Search Fallback
        search_query = f"{brand} {pname}"
        img_url = search_ddg_image(search_query)
        if img_url:
            try:
                resp = requests.get(img_url, headers=HEADERS, timeout=8)
                if resp.status_code == 200 and len(resp.content) > 2048:
                    raw_img = Image.open(io.BytesIO(resp.content)).convert('RGBA')
                    ok = process_and_save_image(raw_img, target_rel)
                    if ok:
                        checkpoint[k]['image_path'] = target_rel
                        checkpoint[k]['status'] = 'RECOVERED_WEB_SEARCH'
                        checkpoint[k]['error'] = None
                        recovered += 1
                        print(f"Recovered [{k}]: {pname} via Web Search -> {target_rel}")
                        continue
            except Exception as e:
                pass

    print(f"\nRecovery Complete! Successfully recovered {recovered} / {len(failed_keys)} failed items.")
    
    # Save checkpoint
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2)
        
    # Update Excel
    print("Updating Verified_Products_FINAL-1.xlsx with recovered paths...")
    wb_write = openpyxl.load_workbook(EXCEL_FILE)
    ws_write = wb_write.active
    
    col_headers = [ws_write.cell(1, c).value for c in range(1, ws_write.max_column + 1)]
    img_col_idx = col_headers.index('Product Image Filename / URL') + 1
    
    total_valid = 0
    for r_idx in range(2, ws_write.max_row + 1):
        r_str = str(r_idx)
        if r_str in checkpoint and checkpoint[r_str].get('image_path'):
            ws_write.cell(r_idx, img_col_idx, checkpoint[r_str]['image_path'])
            total_valid += 1
            
    wb_write.save(EXCEL_FILE)
    print(f"Saved Excel file with {total_valid} / 1806 total valid images!")
    
    # Sync to data/products.json
    try:
        with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
            products = json.load(f)
            
        p_by_name = {p['name'].strip().lower(): p for p in products if p.get('name')}
        p_by_sku = {p['sku'].strip().lower(): p for p in products if p.get('sku')}
        
        synced = 0
        for entry in checkpoint.values():
            pname = entry.get('product_name', '').strip().lower()
            ipath = entry.get('image_path')
            if not ipath: continue
            
            target_p = p_by_name.get(pname)
            if target_p:
                target_p['image'] = ipath
                target_p['gallery'] = [ipath]
                synced += 1
                
        with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2)
        print(f"Updated {synced} products in data/products.json!")
    except Exception as e:
        print(f"Warning syncing products.json: {e}")

if __name__ == '__main__':
    main()
