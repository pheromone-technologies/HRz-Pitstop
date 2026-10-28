import os
import sys
import requests
from PIL import Image
import io

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DOWNLOADS = [
    (
        'https://cdn.shopify.com/s/files/1/0582/1104/1303/files/42_9b8e0133-b2b9-4810-b810-bf71bd8552a6.jpg?v=1775893644',
        'images/legundary_customs/lcb_ns400_gopher_carrier.webp'
    ),
    (
        'https://www.ridersindia.com/cdn/shop/files/Axor_Apex_Hex_2_helmet_white_red_ISI_ECE_DOT_certified.jpg?v=1776959277',
        'images/axor_helmets/axor_apex_hex_white_red.webp'
    ),
    (
        'https://cdn.shopify.com/s/files/1/1459/5894/files/SUPERTOURER-MA-231-1.webp?v=1737182645',
        'images/smk/smk_typhoon_supertourer_gl231.webp'
    ),
    (
        'https://cdn.shopify.com/s/files/1/1459/5894/products/1361_1811.png?v=1651233287',
        'images/smk/smk_retro_ranko_gl213.webp'
    ),
    (
        'https://statmo.in/wp-content/uploads/2022/02/Pidilite-Brite-O-Super-25g-600x607.jpg',
        'images/cleaning/brite_o_super_25g.webp'
    ),
    (
        'https://assets.otrstore.in/images/products/yamaha-r15-v3-mt15-bent-pipe-middle-pipe.jpg',
        'images/performance/r15_v3_mt15_bend_pipe_bs6.webp'
    ),
    (
        'https://royalenfield.store/media/catalog/product/G/L/GLO230007-BLACK_2_HERO.jpg',
        'images/royal_enfield/urban_hustler_v2_black_gloves.webp'
    )
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

BASE_DIR = r"E:\coad\hrx website 2"

for url, dest_rel in DOWNLOADS:
    dest_path = os.path.join(BASE_DIR, dest_rel.replace('/', os.sep))
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 1024:
            im = Image.open(io.BytesIO(r.content))
            im.save(dest_path, 'WEBP', quality=92)
            print(f"[OK] Downloaded {dest_rel} ({im.size}, {len(r.content)} bytes)")
        else:
            print(f"[FAIL] HTTP {r.status_code} for {url}")
    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
