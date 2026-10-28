import json

with open('_vault_archive/scraper_working_cache/scraped_verified_results.json', 'r', encoding='utf-8') as f:
    scraped = json.load(f)

print(f"Loaded {len(scraped)} items from scraped_verified_results.json")
if isinstance(scraped, dict):
    items = scraped.items()
elif isinstance(scraped, list):
    items = enumerate(scraped)

for k, item in items:
    name = (item.get('title') or item.get('name') or '').lower()
    if 'apache' in name and 'rtx' in name:
        print(f"Item: {item.get('title') or item.get('name')}")
        print(f"  URL: {item.get('url') or item.get('product_url')}")
        print(f"  Images: {item.get('images') or item.get('image_urls') or item.get('image')}")
