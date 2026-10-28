import json

with open('_vault_archive/scraper_working_cache/scraped_verified_results.json', 'r', encoding='utf-8') as f:
    scraped = json.load(f)

print("First item keys:", scraped[0].keys() if scraped else "empty")
lcb_count = 0
for item in scraped:
    t = (item.get('title') or item.get('product_name') or item.get('name') or '').lower()
    if 'lcb' in t or 'legundary' in t or 'apache' in t:
        lcb_count += 1
        if lcb_count <= 10:
            print(f"Title: {item.get('title') or item.get('name')}, Images: {item.get('images') or item.get('image')}")
print(f"Total matching: {lcb_count}")
