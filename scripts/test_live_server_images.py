import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
base = 'http://localhost:8000'

try:
    res = urllib.request.urlopen(f'{base}/data/products.json')
    prods = json.loads(res.read().decode('utf-8'))
    prod_map = {p['id']: p for p in prods}
except Exception as e:
    print(f"Failed to fetch products.json from {base}: {e}")
    sys.exit(1)

targets = [
    'hrz-lcb-tvs-apache-rtx-300-vambrace-bash-plate-sliver-1438',
    'hrz-lcb-tvs-apache-rtx-300-vambrace-bash-plate-white-1440',
    'hrz-lcb-tvs-apache-rtx-300-vambrace-bash-plate-black-1436',
    'hrz-lcb-tvs-apache-rtx-300-vector-radiator-grill-black-1444',
    'hrz-lcb-tvs-apache-rtx-300-vector-radiator-gril-silver-1442',
    'hrz-lcb-v-strom-adrinex-crash-guard-with-slider-1446',
    'hrz-lcb-v-strom-vambrace-bashplate-1458',
    'hrz-lcb-x-pulse-200-4v-pro-cosmic-headlight-grill-1456',
    'hrz-lcb-x-pulse-headlight-grill-1465'
]

print("=== Checking Live Server Products & Images ===")
all_ok = True
for pid in targets:
    p = prod_map.get(pid)
    if not p:
        print(f"MISSING: {pid}")
        all_ok = False
        continue
    img_rel = p.get('image', '')
    img_url = f"{base}/{img_rel}"
    try:
        img_res = urllib.request.urlopen(img_url)
        content_len = len(img_res.read())
        print(f"OK [HTTP {img_res.status}]: {p.get('name')} -> {img_rel} ({content_len} bytes)")
    except Exception as e:
        print(f"FAIL: {p.get('name')} -> {img_url} Error: {e}")
        all_ok = False

if all_ok:
    print("\nALL TARGET PRODUCTS AND IMAGES SERVED SUCCESSFULLY!")
