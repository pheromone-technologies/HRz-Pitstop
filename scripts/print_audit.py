import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/image_audit_results.json', encoding='utf-8') as f:
    res = json.load(f)

print("=" * 60)
print(f"1. Cutout wiped out by Rembg ({len(res['mostly_transparent_cutout'])} items)")
print("These are products where rembg mistakenly removed the product itself:")
print("=" * 60)
for item in res['mostly_transparent_cutout']:
    print(f"  [{item['category']}] {item['name'][:45]}")
    print(f"     Path: {item['path']} (coverage: {item['product_coverage_pct']}%)")

print("\n" + "=" * 60)
print(f"2. Tiny / Stub Files (<3.5KB) ({len(res['tiny_files'])} items)")
print("These are corrupted stubs or empty files:")
print("=" * 60)
for item in res['tiny_files']:
    print(f"  [{item['category']}] {item['name'][:45]}")
    print(f"     Path: {item['path']} ({item.get('size_bytes', 0)} bytes)")

print("\n" + "=" * 60)
print(f"3. Extreme Aspect Ratios ({len(res['distorted_aspect'])} items)")
print("=" * 60)
for item in res['distorted_aspect']:
    print(f"  [{item['category']}] {item['name'][:45]} | {item['dims']} (ratio {item['ratio']})")
    print(f"     Path: {item['path']}")
