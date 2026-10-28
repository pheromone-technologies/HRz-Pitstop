import os
import json
import urllib.request
from PIL import Image
import numpy as np

headers = {'User-Agent': 'Mozilla/5.0'}

def make_clean_square(im, target_size=1080):
    im = im.convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    corners = np.vstack([arr[:25, :25], arr[:25, -25:], arr[-25:, :25], arr[-25:, -25:]])
    bg_color = np.median(corners.reshape(-1, 3), axis=0).astype(int)
    diff = np.sqrt(np.sum((arr.astype(int) - bg_color)**2, axis=2))
    content_mask = diff > 25
    
    if np.any(content_mask):
        ys, xs = np.where(content_mask)
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        cw, ch = (xmax - xmin + 1), (ymax - ymin + 1)
        content = im.crop((xmin, ymin, xmax + 1, ymax + 1))
        max_dim = max(cw, ch)
        pad = int(max_dim * 0.12)
        side = max_dim + pad * 2
        canvas_bg = (255, 255, 255) if np.mean(bg_color) > 210 else tuple(int(c) for c in bg_color)
        square = Image.new('RGB', (side, side), canvas_bg)
        square.paste(content, ((side - cw) // 2, (side - ch) // 2))
        return square.resize((target_size, target_size), Image.Resampling.LANCZOS)
    else:
        max_dim = max(w, h)
        square = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
        square.paste(im, ((max_dim - w) // 2, (max_dim - h) // 2))
        return square.resize((target_size, target_size), Image.Resampling.LANCZOS)

def download_and_process(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    temp_path = dest_path + '.temp'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(temp_path, 'wb') as f:
        f.write(resp.read())
    raw_im = Image.open(temp_path)
    final_im = make_clean_square(raw_im)
    final_im.save(dest_path, 'WEBP', quality=92)
    if os.path.exists(temp_path):
        os.remove(temp_path)
    print(f"Processed: {dest_path}")

ktm_targets = {
    'hrz-lcb-ktm-adv-390-2025-raptor-crashgaurd-1290': {
        'url': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_86e2bc52-60c1-41ee-93fd-b3bd37252be1.jpg?v=1767592173',
        'file': 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_raptor_crashgaurd_orange_1.webp'
    },
    'hrz-lcb-ktm-adv-390-2025-vector-radiator-grill-1312': {
        'url': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_00fa79de-c167-4a41-939e-d409d179ec76.jpg?v=1767592097',
        'file': 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_vector_radiator_grill_black_1.webp'
    },
    'hrz-lcb-ktm-adv-390-2025-vambrace-bashplate-1311': {
        'url': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_f2726f1a-3ae2-4e71-9fd8-7b800f58aee1.jpg?v=1767592334',
        'file': 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_vambrace_bashplate_1.webp'
    },
    'hrz-lcb-ktm-adv-390-2025-cosmic-headlight-grill-1296': {
        'url': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_7ad8cff5-6ac0-42a1-bbb7-e02f9ce5dbaf.jpg?v=1767592250',
        'file': 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_cosmic_headlight_grill_1.webp'
    },
    'hrz-lcb-ktm-adv-390-2025-casus-saddle-stay-1294': {
        'url': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_6df65bb1-d20e-4c7a-baf6-ea2d23e01dfb.jpg?v=1767592350',
        'file': 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_casus_saddle_stay_1.webp'
    },
    'hrz-lcb-ktm-adv-390-2025-ploigos-gps-mount-1305': {
        'url': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/6_44c6b1b4-cfbb-4e09-95a6-bcf560a8786d.jpg?v=1767592085',
        'file': 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_ploigos_gps_mount_1.webp'
    },
    'hrz-lcb-ktm-adv-390-2025-gopher-luggage-carrier-1301': {
        'url': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_70bbfa65-bed6-4f74-9ffd-e1649e7a7284.jpg?v=1767592317',
        'file': 'images_processed/catalog/lcb/lcb_ktm_adv_390_2025_gopher_luggage_carrier_1.webp'
    },
}

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

prod_by_id = {p['id']: p for p in products}

for pid, cfg in ktm_targets.items():
    if pid not in prod_by_id:
        continue
    download_and_process(cfg['url'], cfg['file'])
    p = prod_by_id[pid]
    p['image'] = cfg['file']
    p['gallery'] = [cfg['file']]
    print(f"Updated KTM product {pid} -> {cfg['file']}")

with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

if os.path.exists('test design site/data/products.json'):
    with open('test design site/data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

print("KTM products updated!")
