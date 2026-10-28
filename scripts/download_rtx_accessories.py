import urllib.request
import os
from PIL import Image

headers = {'User-Agent': 'Mozilla/5.0'}
os.makedirs('scratch/image_candidates', exist_ok=True)

downloads = {
    # Raptor crash guards
    'rtx_raptor_black': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_4e00ee05-6657-4df2-8487-4bba3714600c.webp?v=1771825811',
    'rtx_raptor_red': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_a7989ce6-e82c-4020-b1c0-2080eb59ca93.webp?v=1771595667',
    'rtx_raptor_white': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_16f2391a-191c-4953-8b20-f8de056909a2.webp?v=1771495075',
    
    # Accessories
    'rtx_footrest': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/FOO25816_02.jpg?v=1770967729',
    'rtx_rear_oil_cap': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/oil_cap_3d92ece8-f4fd-40a2-b242-53528dade1f5.webp?v=1771825949',
    'rtx_front_oil_cap': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/CAP25806_03.jpg?v=1770968056',
    'rtx_stand_base': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_80dc2a9d-f5a4-41ef-a9f4-500bc29a7193.jpg?v=1770885500',
    'rtx_gps_mount': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/MOB25817_01.jpg?v=1770967717',
}

for name, url in downloads.items():
    ext = '.webp' if '.webp' in url else '.jpg'
    dest = f"scratch/image_candidates/{name}{ext}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp, open(dest, 'wb') as f:
            f.write(resp.read())
        im = Image.open(dest)
        print(f"Downloaded {name}: size={im.size}")
    except Exception as e:
        print(f"Failed {name}: {e}")
