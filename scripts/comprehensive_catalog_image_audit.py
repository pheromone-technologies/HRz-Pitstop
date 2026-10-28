import json
import os
import hashlib
from collections import defaultdict
from PIL import Image

def get_file_md5(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

def analyze_catalog():
    with open('data/products.json', encoding='utf-8') as f:
        products = json.load(f)

    print(f"Total products in catalog: {len(products)}")

    # 1. Check duplicate image paths in products.json
    path_to_products = defaultdict(list)
    for p in products:
        img = p.get('image', '').strip()
        if img:
            path_to_products[img].append(p)

    shared_paths = {path: prods for path, prods in path_to_products.items() if len(prods) > 1}
    print(f"\n--- 1. Shared Image Paths (exact same file path assigned to multiple products): {len(shared_paths)} paths ---")
    total_shared_path_prods = sum(len(prods) for prods in shared_paths.values())
    print(f"Total products sharing paths: {total_shared_path_prods}")

    # 2. Check identical MD5 hashes across different filenames
    hash_to_files = defaultdict(set)
    hash_to_products = defaultdict(list)
    for p in products:
        img = p.get('image', '').strip()
        if not img:
            continue
        filepath = img.replace('/', os.sep)
        h = get_file_md5(filepath)
        if h:
            hash_to_files[h].add(img)
            hash_to_products[h].append(p)

    shared_hashes = {h: prods for h, prods in hash_to_products.items() if len(prods) > 1}
    print(f"\n--- 2. Identical Image Content (same MD5 hash across products): {len(shared_hashes)} unique images ---")
    total_shared_hash_prods = sum(len(prods) for prods in shared_hashes.values())
    print(f"Total products sharing identical image content: {total_shared_hash_prods}")

    # Let's inspect which categories have the most duplicates
    cat_dup_counts = defaultdict(int)
    for h, prods in shared_hashes.items():
        # Only count if the product names are actually different (ignoring exact identical products/variants)
        names = {p['name'].strip() for p in prods}
        if len(names) > 1:
            for p in prods:
                cat_dup_counts[p.get('category', 'Unknown')] += 1

    print("\nDuplicates across DIFFERENT product names by category:")
    for cat, count in sorted(cat_dup_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} products")

    # Output detailed report into scratch/catalog_duplicate_audit.json
    report = []
    for h, prods in shared_hashes.items():
        names = list({p['name'].strip() for p in prods})
        if len(names) > 1:
            report.append({
                'hash': h,
                'files': list(hash_to_files[h]),
                'products': [{'id': p['id'], 'name': p['name'], 'category': p.get('category'), 'image': p.get('image')} for p in prods]
            })

    with open('scratch/catalog_duplicate_audit.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved {len(report)} duplicate clusters to scratch/catalog_duplicate_audit.json")

if __name__ == '__main__':
    analyze_catalog()
