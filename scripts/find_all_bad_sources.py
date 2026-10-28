import json

with open('tools/output/verified_images_checkpoint.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

bad_sources = []
for k, v in data.items():
    src = str(v.get('source') or '').lower()
    pname = v.get('product_name')
    path = v.get('image_path')
    if any(b in src for b in ['a.webp', 'banner', 'logo', 'autonity.in/cdn/shop/files/a', 'autowarrior.in/cdn/shop/files/you_tube']):
        bad_sources.append((k, pname, path, src))

print(f"Total bad sources in checkpoint: {len(bad_sources)}")
for b in bad_sources:
    print(f"  Row {b[0]}: {b[1]}")
    print(f"    Path: {b[2]}")
    print(f"    Source: {b[3]}")
