import json

with open('_vault_archive/scraper_working_cache/scraped_verified_results.json', 'r', encoding='utf-8') as f:
    scraped = json.load(f)

brands = {}
for item in scraped:
    b = item.get('brand') or item.get('vendor') or 'Unknown'
    brands[b] = brands.get(b, 0) + 1

print("Brands in scraped_verified_results:", brands)

for item in scraped:
    pos = (item.get('pos_product_name') or '').lower()
    off = (item.get('official_title') or '').lower()
    if 'apache' in pos or 'apache' in off or 'rtx' in pos or 'rtx' in off:
        print(f"POS: {item.get('pos_product_name')} | Official: {item.get('official_title')}")
        print(f"  Img: {item.get('image_path')}")
        print(f"  URL: {item.get('source_url')}")
