import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/image_audit_results.json', encoding='utf-8') as f:
    res = json.load(f)

all_bad = {}

for item in res['mostly_transparent_cutout']:
    all_bad[item['id']] = {
        'name': item['name'],
        'cat': item['category'],
        'path': item['path'],
        'issue': f"Rembg erased product ({item['product_coverage_pct']} pct coverage left)"
    }

for item in res['tiny_files']:
    if item['id'] not in all_bad:
        all_bad[item['id']] = {
            'name': item['name'],
            'cat': item['category'],
            'path': item['path'],
            'issue': f"Tiny stub file ({item.get('size_bytes', 0)} bytes)"
        }

for item in res['distorted_aspect']:
    if item['id'] not in all_bad:
        all_bad[item['id']] = {
            'name': item['name'],
            'cat': item['category'],
            'path': item['path'],
            'issue': f"Extreme banner aspect ratio ({item['dims']}, ratio {item['ratio']})"
        }

print(f"Total unique affected products: {len(all_bad)} (out of 1,749 total)")

by_cat = {}
for p in all_bad.values():
    by_cat[p['cat']] = by_cat.get(p['cat'], 0) + 1

print("\nBreakdown by category:")
for cat, c in sorted(by_cat.items(), key=lambda x: -x[1]):
    print(f"  - {cat}: {c} products")

print("\nDetailed List of All Affected Products:")
for idx, (p_id, p_info) in enumerate(all_bad.items(), 1):
    print(f"{idx:2d}. [{p_info['cat']}] {p_info['name']}")
    print(f"    Issue: {p_info['issue']}")
    print(f"    Path : {p_info['path']}")

# Save detailed list to scratch/bad_images_summary.json
with open('scratch/bad_images_summary.json', 'w', encoding='utf-8') as f:
    json.dump(all_bad, f, indent=2, ensure_ascii=False)
