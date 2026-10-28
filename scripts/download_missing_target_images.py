import os
import sys
import requests
from PIL import Image
import io

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DOWNLOADS = [
    (
        'https://cdn.shopify.com/s/files/1/0549/0937/0479/files/y07.png?v=1749048182',
        'images/carbonado/carbonado_y07_backpack.webp'
    ),
    (
        'https://cdn.shopify.com/s/files/1/0519/0084/2163/files/BAG0059_1.jpg?v=1755630394',
        'images/ogio/ogio_backpack.webp'
    ),
    (
        'https://www.apollotyres.com/content/dam/orbit/syncforce/products/2062/T0016906.png',
        'images/apollo/apollo_tramplr_xr.webp'
    ),
    (
        'https://cdn.shopify.com/s/files/1/0691/4818/0694/files/Stretchyourlimitsincrimson.png?v=1792835439',
        'images/66_bhp/66_bhp_hand_sleeve.webp'
    )
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for url, dest in DOWNLOADS:
    dest_path = os.path.join(r"E:\coad\hrx website 2", dest.replace('/', os.sep))
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 1024:
            im = Image.open(io.BytesIO(r.content))
            im.save(dest_path, 'WEBP', quality=90)
            print(f"[OK] Downloaded {dest} ({im.size}, {len(r.content)} bytes)")
        else:
            print(f"[FAIL] HTTP {r.status_code} for {url}")
    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
