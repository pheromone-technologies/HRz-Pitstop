#!/usr/bin/env python3
"""
Clean Product Images Background & Remove Competitor Logos
Repo: HRz Pitstop (E:\\coad\\hrx website 2)

Scans all product images used in data/products.json,
identifies images on white background with competitor logos/watermarks in corners,
removes the background and watermarks using rembg,
and composites the isolated product onto a clean, custom white background.
"""

import os
import sys
import json
from PIL import Image
import numpy as np
from rembg import remove
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")

print("=" * 70)
print("HRZ PITSTOP: PRODUCT IMAGE CLEANUP & WATERMARK REMOVAL")
print("=" * 70)

with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
    products = json.load(f)

unique_images = set()
for p in products:
    if p.get('image'): unique_images.add(p['image'])
    for g in p.get('gallery', []):
        if g: unique_images.add(g)

print(f"Total unique images referenced in catalog: {len(unique_images)}")

# Identify images with white/light background and corner watermarks
def is_watermarked_on_white(rel_path):
    full = os.path.join(BASE_DIR, rel_path.replace('/', os.sep))
    if not os.path.exists(full):
        return False, None
    try:
        im = Image.open(full).convert('RGB')
        w, h = im.size
        if w < 100 or h < 100:
            return False, None
            
        arr = np.array(im)
        
        # Check border white ratio
        top_edge = arr[0:5, :, :]
        bottom_edge = arr[-5:, :, :]
        left_edge = arr[:, 0:5, :]
        right_edge = arr[:, -5:, :]
        
        border_pixels = np.concatenate([
            top_edge.reshape(-1, 3), bottom_edge.reshape(-1, 3),
            left_edge.reshape(-1, 3), right_edge.reshape(-1, 3)
        ])
        white_border_ratio = np.mean(np.all(border_pixels > 235, axis=-1))
        
        # Check folders known to contain competitor badges (LCB, MotoTorque, Bandidos)
        is_known_vendor = any(k in rel_path.lower() for k in [
            'legundary', 'lcb', 'mototorque', 'moto_torque', 'cramster', 'bandidos'
        ])
        
        if white_border_ratio > 0.60 or is_known_vendor:
            cw, ch = int(w * 0.18), int(h * 0.18)
            corners = {
                'TL': arr[0:ch, 0:cw, :],
                'TR': arr[0:ch, -cw:, :],
                'BL': arr[-ch:, 0:cw, :],
                'BR': arr[-ch:, -cw:, :]
            }
            
            for cname, cbox in corners.items():
                non_white = np.mean(~np.all(cbox > 235, axis=-1))
                if 0.03 < non_white < 0.45:
                    return True, cname
                    
        return False, None
    except Exception:
        return False, None

print("\nScanning images for competitor watermarks & logos...")
candidates = []
for p in sorted(unique_images):
    has_wm, corner = is_watermarked_on_white(p)
    if has_wm:
        candidates.append((p, corner))

print(f"Identified {len(candidates)} images with competitor logos on white background.")

def clean_image(item):
    rel_path, corner = item
    full = os.path.join(BASE_DIR, rel_path.replace('/', os.sep))
    try:
        orig = Image.open(full).convert('RGBA')
        w, h = orig.size
        
        # Optional: pre-zero the specific corner containing the watermark if outside the center
        # This prevents any edge text from surviving segmentation
        orig_arr = np.array(orig)
        cw, ch = int(w * 0.15), int(h * 0.15)
        if corner == 'TL': orig_arr[0:ch, 0:cw, :] = [255, 255, 255, 255]
        elif corner == 'TR': orig_arr[0:ch, -cw:, :] = [255, 255, 255, 255]
        elif corner == 'BL': orig_arr[-ch:, 0:cw, :] = [255, 255, 255, 255]
        elif corner == 'BR': orig_arr[-ch:, -cw:, :] = [255, 255, 255, 255]
        
        pre_cleaned = Image.fromarray(orig_arr)
        
        # Remove background with rembg
        nobg = remove(pre_cleaned)
        
        # Composite onto custom clean white canvas
        white_bg = Image.new('RGBA', nobg.size, (255, 255, 255, 255))
        composite = Image.alpha_composite(white_bg, nobg).convert('RGB')
        
        # Overwrite in place with optimized WebP
        composite.save(full, 'WEBP', quality=90)
        return True, rel_path
    except Exception as e:
        return False, f"{rel_path}: {e}"

print(f"\nProcessing {len(candidates)} images to remove backgrounds and apply custom white bg...")
success_count = 0
failed_count = 0

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(clean_image, item): item for item in candidates}
    for future in as_completed(futures):
        ok, res = future.result()
        if ok:
            success_count += 1
            if success_count % 25 == 0 or success_count == len(candidates):
                print(f"   Cleaned {success_count}/{len(candidates)} images...")
        else:
            failed_count += 1

print("\n" + "=" * 70)
print(f"CLEANUP COMPLETE: {success_count} images successfully sanitized with custom white background!")
if failed_count:
    print(f"Failed images: {failed_count}")
print("=" * 70)
