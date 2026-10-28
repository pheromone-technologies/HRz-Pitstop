import json
import os
import hashlib

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

lcb_prods = [p for p in products if p.get('brand') in ['LCB', 'Legundary']]
print(f"Total LCB/Legundary products: {len(lcb_prods)}")

# Check duplicate images among LCB products
hashes = {}
for p in lcb_prods:
    img = p.get('image', '')
    if img and os.path.exists(img):
        h = hashlib.md5(open(img, 'rb').read()).hexdigest()
        hashes.setdefault(h, []).append(p)

print("\nDuplicate LCB product groups:")
for h, plist in hashes.items():
    if len(plist) > 1:
        print(f"\nHash {h[:10]} ({len(plist)} products): {plist[0].get('image')}")
        for p in plist:
            print(f"   [{p.get('id')}] {p.get('name')}")
