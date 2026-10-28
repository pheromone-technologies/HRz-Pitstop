import json
import os

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print("Checking Luggage & Touring products:")
for p in products:
    cat = p.get('category', '')
    price = p.get('price', 0)
    img = p.get('image', '')
    name = p.get('name', '')
    if 'Luggage' in cat:
        # Check price 1500 or adjacent
        if price == 1500 or 'warrior' in name.lower() or 'auto' in name.lower() or 'warrior' in img.lower():
            print(f"ID: {p['id']} | Name: {name} | Price: {price} | Img: {img}")

# Also search all files in images/ and images_processed/ for any image named warrior or containing auto
print("\nSearching disk for 'warrior' or 'auto' images:")
for root, dirs, files in os.walk('.'):
    if any(k in root for k in ['.git', '.venv', '_vault_archive']):
        continue
    for f in files:
        fl = f.lower()
        if ('warrior' in fl or 'autowarrior' in fl) and fl.endswith(('.webp', '.png', '.jpg')):
            print(f"  Disk Image: {os.path.join(root, f)}")
