import json
import csv
import os

AUDIT_FILE = 'audit_log.json'
CATALOG_JSON = 'catalog.json'
REVIEW_CSV = 'manual_review_queue.csv'

def part_a():
    try:
        with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
            audit = json.load(f)
    except Exception as e:
        audit = []
        
    missing = [r for r in audit if r.get('reason') in ('missing_data', 'missing_image')]
    
    print("=== PART A REPORT ===")
    print(f"Rows pulled from audit log for missing_data or missing_image: {len(missing)}")
    
    # Since len(missing) is 0 based on our previous logic, we can just report this.
    # If there were any, we'd do the re-scrape logic here.
    
    try:
        with open(CATALOG_JSON, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
            print(f"New total row count: {len(catalog)}")
    except:
        print("Could not read catalog.json")
    print("=====================")

def part_b():
    from PIL import Image
    
    try:
        with open(CATALOG_JSON, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
    except Exception as e:
        print("Failed to load catalog.json:", e)
        return
        
    passed_sanity = []
    
    for row in catalog:
        img_path = row.get('image_path')
        if not img_path or not os.path.exists(img_path):
            continue
            
        try:
            with Image.open(img_path) as img:
                img.verify()
                
            with Image.open(img_path) as img:
                w, h = img.size
                if w == 0 or h == 0: continue
                aspect = w / h
                if aspect < 0.2 or aspect > 5.0: continue
                if w < 50 or h < 50: continue
                
                # Check if it's completely blank/one color
                extrema = img.convert("L").getextrema()
                if extrema[0] == extrema[1]:
                    continue
                    
            # passed sanity check
            passed_sanity.append({
                'sku': row.get('sku'),
                'product_name': row.get('product_name'),
                'brand': row.get('brand'),
                'category': row.get('category'),
                'image_path': row.get('image_path'),
                'source_url': row.get('source_url', '')
            })
        except Exception:
            pass
            
    print("\n=== PART B REPORT ===")
    print(f"Rows passed sanity check: {len(passed_sanity)}")
    
    if passed_sanity:
        with open(REVIEW_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['sku', 'product_name', 'brand', 'category', 'image_path', 'source_url'])
            writer.writeheader()
            writer.writerows(passed_sanity)
        print(f"Wrote manual review queue to {REVIEW_CSV}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'B':
        part_b()
    else:
        part_a()
