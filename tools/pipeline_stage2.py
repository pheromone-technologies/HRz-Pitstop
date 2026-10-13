import json
import os
import sys
import uuid
from collections import defaultdict
import subprocess

STAGING_FILE = 'staging.json'
AUDIT_FILE = 'audit_log.json'
FINAL_JSON = 'catalog.json'
FINAL_CSV = 'catalog.csv'
WATERMARK_SCRIPT = 'E:\\coad\\tools for hrz\\image logo editor\\process_images.py'
WATERMARK_IMAGE = 'E:\\coad\\tools for hrz\\image logo editor\\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png'
OUTPUT_IMAGES_DIR = 'images_processed'

def process_deletions(approved_statuses):
    with open(STAGING_FILE, 'r', encoding='utf-8') as f:
        staging = json.load(f)
        
    surviving = []
    deleted = []
    
    for row in staging:
        if row['status'] in approved_statuses:
            deleted.append({
                "sku": row.get('sku'),
                "product_name": row.get('product_name'),
                "image_ref": row.get('image_path') or row.get('source_url'),
                "reason": row['status']
            })
        else:
            surviving.append(row)
            
    if deleted:
        audit = []
        if os.path.exists(AUDIT_FILE):
            with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
                try: audit = json.load(f)
                except: pass
        audit.extend(deleted)
        with open(AUDIT_FILE, 'w', encoding='utf-8') as f:
            json.dump(audit, f, indent=2)
            
    with open(STAGING_FILE, 'w', encoding='utf-8') as f:
        json.dump(surviving, f, indent=2)
        
    print(f"Deleted {len(deleted)} rows. Saved to audit log.")
    return surviving

def compress_and_watermark(staging):
    # Prepare script path to image logo editor
    sys.path.append(os.path.dirname(WATERMARK_SCRIPT))
    import process_images
    
    for row in staging:
        if row['status'] == 'clean':
            input_path = row['image_path']
            if not input_path or not os.path.exists(input_path):
                continue
                
            # Compress and watermark
            rel_dir = row['brand'].lower().replace(' ', '_')
            output_dir = OUTPUT_IMAGES_DIR
            
            # Call process_single_image
            result = process_images.process_single_image(
                input_path=input_path,
                output_dir=output_dir,
                rel_dir=rel_dir,
                watermark_path=WATERMARK_IMAGE,
                max_size=(1000, 1000), # from existing process_images defaults maybe?
                padding=20,
                scale_factor=0.15,
                quality=80
            )
            
            if result and isinstance(result, tuple) and len(result) == 3 and result[2]:
                print(f"Error processing image {input_path}: {result[2]}")
                continue
                
            # If successful, output path is constructed the same way
            filename = os.path.basename(input_path)
            name, _ = os.path.splitext(filename)
            new_filename = f"{name}.webp"
            final_path = os.path.join(output_dir, rel_dir, new_filename)
            
            if os.path.exists(final_path):
                row['image_path'] = final_path
                row['source_url'] = ""

    with open(STAGING_FILE, 'w', encoding='utf-8') as f:
        json.dump(staging, f, indent=2)
        
    print("Compression and watermarking complete.")
    return staging

def final_verification(staging, target_category):
    # ALLOWED_BRANDS map for verification
    ALLOWED_BRANDS = {
        "Helmets": ["Axor", "SMK", "KYT", "Steelbird", "Vega", "Studds", "Royal Enfield"],
        "Gloves": ["Raida", "Cramster", "Axor", "Royal Enfield", "100%", "Fox", "DSG", "Scala", "Lone Ranger"],
        "Jackets": ["DSG", "Lone Ranger", "Raida", "Axor", "Cramster", "Scala"],
        "Tank bags": ["Raida", "Cramster", "Wild Heart", "Axor", "Moto Torque"],
        "Crash guards": ["Legundary Customs", "Moto Torque", "Bizen", "Moto Care", "MTechnics"],
        "Lubricants/Oils": ["AMS", "Motul", "Motomax"]
    }
    allowed_brands = [b.lower() for b in ALLOWED_BRANDS.get(target_category, [])]
    
    verified = []
    failed = []
    seen = set()
    
    for row in staging:
        if row['status'] != 'clean':
            failed.append((row['product_name'], f"Status is {row['status']} instead of clean"))
            continue
            
        if row['category'] != target_category:
            failed.append((row['product_name'], "Category mismatch"))
            continue
            
        if not row['brand'] or row['brand'].lower() not in allowed_brands:
            failed.append((row['product_name'], "Brand mismatch"))
            continue
            
        # check all schema fields populated
        if not all(row.get(k) is not None and str(row.get(k)).strip() != "" for k in ['brand', 'category', 'product_name', 'mrp', 'sku']):
            failed.append((row['product_name'], "Missing required text fields"))
            continue
            
        # check image_path exists and is webp
        if not row['image_path'] or not row['image_path'].endswith('.webp') or not os.path.exists(row['image_path']):
            failed.append((row['product_name'], "Image path invalid or missing"))
            continue
            
        # check source_url dropped
        if row.get('source_url'):
            failed.append((row['product_name'], "Source URL not dropped"))
            continue
            
        # check duplicates
        dup_key = (row['brand'], row['category'], row['product_name'], row['variant'])
        if dup_key in seen:
            failed.append((row['product_name'], "Duplicate found"))
            continue
        seen.add(dup_key)
        
        verified.append(row)
        
    print(f"=== STEP 9 REPORT ===")
    print(f"Verified rows: {len(verified)}")
    print(f"Failed rows: {len(failed)}")
    for name, reason in failed[:5]:
        print(f" - {name}: {reason}")
    if len(failed) > 5:
        print(f"   ... and {len(failed) - 5} more")
        
    return verified, failed

def write_output(verified):
    # write to JSON
    out_json = []
    for r in verified:
        out_json.append({
            "brand": r['brand'],
            "category": r['category'],
            "product_name": r['product_name'],
            "model": r.get('model', ''),
            "variant": r.get('variant', 'Standard'),
            "sku": r['sku'],
            "mrp": r['mrp'],
            "image_path": r['image_path'],
            "source_url": r.get('source_url', '')
        })
        
    # Append to catalog.json
    existing_json = []
    if os.path.exists(FINAL_JSON):
        with open(FINAL_JSON, 'r', encoding='utf-8') as f:
            try: existing_json = json.load(f)
            except: pass
    existing_json.extend(out_json)
    
    with open(FINAL_JSON, 'w', encoding='utf-8') as f:
        json.dump(existing_json, f, indent=2)
        
    # Append to catalog.csv
    file_exists = os.path.exists(FINAL_CSV)
    import csv
    with open(FINAL_CSV, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["brand", "category", "product_name", "model", "variant", "sku", "mrp", "image_path", "source_url"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(out_json)
        
    print("Wrote output successfully.")

if __name__ == "__main__":
    action = sys.argv[1]
    
    if action == "delete":
        approved = sys.argv[2].split(',')
        staging = process_deletions(approved)
    elif action == "compress":
        with open(STAGING_FILE, 'r', encoding='utf-8') as f:
            staging = json.load(f)
        compress_and_watermark(staging)
    elif action == "verify":
        cat = sys.argv[2]
        with open(STAGING_FILE, 'r', encoding='utf-8') as f:
            staging = json.load(f)
        verified, failed = final_verification(staging, cat)
    elif action == "write":
        cat = sys.argv[2]
        with open(STAGING_FILE, 'r', encoding='utf-8') as f:
            staging = json.load(f)
        verified, _ = final_verification(staging, cat)
        write_output(verified)
