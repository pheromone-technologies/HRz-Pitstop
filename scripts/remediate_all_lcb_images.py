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
    
    # Estimate background color from corners
    corners = np.vstack([arr[:25, :25], arr[:25, -25:], arr[-25:, :25], arr[-25:, -25:]])
    bg_color = np.median(corners.reshape(-1, 3), axis=0).astype(int)
    
    # Content mask
    diff = np.sqrt(np.sum((arr.astype(int) - bg_color)**2, axis=2))
    content_mask = diff > 25
    
    if np.any(content_mask):
        ys, xs = np.where(content_mask)
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        
        # If the content box is already occupying most of the image, don't over-crop
        cw, ch = (xmax - xmin + 1), (ymax - ymin + 1)
        content = im.crop((xmin, ymin, xmax + 1, ymax + 1))
        
        # 12% padding on the largest dimension
        max_dim = max(cw, ch)
        pad = int(max_dim * 0.12)
        side = max_dim + pad * 2
        
        # Pure white background if near white, else border color
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
    print(f"Processed: {dest_path} (from {url[:60]}...)")

# Define target mappings: product_id -> { 'primary_url': ..., 'gallery_urls': [...] }
targets = {
    # 1. Apache RTX 300 Vambrace Bash Plate (Silver) - ID 1438
    'hrz-lcb-tvs-apache-rtx-300-vambrace-bash-plate-sliver-1438': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/4_68b7fee5-2f47-4dec-aaff-68f5b0b9082c.jpg?v=1770967774',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/4_68b7fee5-2f47-4dec-aaff-68f5b0b9082c.jpg?v=1770967774',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_6fdfecde-bb65-4baa-880a-4fd44d342d22.jpg?v=1770967774',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG25818_02.jpg?v=1770967774'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_sliver'
    },
    
    # 2. Apache RTX 300 Vambrace Bash Plate (White / Raw) - ID 1440
    'hrz-lcb-tvs-apache-rtx-300-vambrace-bash-plate-white-1440': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_9fd8285b-bd14-47ea-b11c-0799fba9c94e.jpg?v=1770967774',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_9fd8285b-bd14-47ea-b11c-0799fba9c94e.jpg?v=1770967774',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_9102d687-bb4a-48dd-b5bf-0a6c9f43b977.jpg?v=1770967774',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG25818_02.jpg?v=1770967774'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_white'
    },
    
    # 3. Apache RTX 300 Vambrace Bash Plate (Black) - ID 1436
    'hrz-lcb-tvs-apache-rtx-300-vambrace-bash-plate-black-1436': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_jpg.jpg?v=1771827821',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_jpg.jpg?v=1771827821',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2.jpg_2.jpg?v=1771827830',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/bash.webp?v=1771827830'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vambrace_bash_plate_black'
    },

    # 4. Apache RTX 300 Vector Radiator Grill (Black) - ID 1444
    'hrz-lcb-tvs-apache-rtx-300-vector-radiator-grill-black-1444': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_aa3c2f73-f84b-481b-939f-c38a9bda2f07.jpg?v=1771828206',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_aa3c2f73-f84b-481b-939f-c38a9bda2f07.jpg?v=1771828206',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/reditor_22.webp?v=1771828206'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vector_radiator_grill_black'
    },

    # 5. Apache RTX 300 Vector Radiator Grill (Silver) - ID 1442
    'hrz-lcb-tvs-apache-rtx-300-vector-radiator-gril-silver-1442': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/WEBSIZEcopy.jpg?v=1770967982',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/WEBSIZEcopy.jpg?v=1770967982',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/RAG25809_03.jpg?v=1770967982'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_vector_radiator_gril_silver'
    },

    # 6. V-Strom Adrinex Crash Guard With Slider - ID 1446
    'hrz-lcb-v-strom-adrinex-crash-guard-with-slider-1446': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/LCBVStromAdrinexCrashguardWithSlider.webp?v=1719981049',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/LCBVStromAdrinexCrashguardWithSlider.webp?v=1719981049',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/CRA8478-legundary-v-strom-crashguard-with-slider2_1ff05a17-f79f-4fd9-8053-9462a2064314.webp?v=1767593142',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/11_d4c11087-735f-4523-bc7b-0fccd7676953.webp?v=1767593142'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_v_strom_adrinex_crash_guard_with_slider'
    },

    # 7. V-Strom Vambrace Bashplate - ID 1458
    'hrz-lcb-v-strom-vambrace-bashplate-1458': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG8482-LEGUNDARY-VSTROM-VAMBRACE-BASH-PLATE.webp?v=1767593106',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG8482-LEGUNDARY-VSTROM-VAMBRACE-BASH-PLATE.webp?v=1767593106',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG8482-LEGUNDARY-VSTROM-VAMBRACE-BASH-PLATE2.webp?v=1719979723',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/14_65647fcb-ea3a-427e-982b-80ca9e68e2d3.webp?v=1767593106'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_v_strom_vambrace_bashplate'
    },

    # 8. X Pulse 200 4V Pro Cosmic Headlight Grill - ID 1456
    'hrz-lcb-x-pulse-200-4v-pro-cosmic-headlight-grill-1456': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_23382af5-ea93-469c-9ee9-75dc82ca1a59.jpg?v=1767590437',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_23382af5-ea93-469c-9ee9-75dc82ca1a59.jpg?v=1767590437',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_116d4824-e0a3-403b-a5fb-989a4ecfb901.jpg?v=1767590437'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_cosmic_headlight_grill'
    },

    # 9. X Pulse Headlight Grill - ID 1465
    'hrz-lcb-x-pulse-headlight-grill-1465': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/hero-xpulse-headlight-grill-lcb2_58980374-b92c-4f7d-9506-8e9bc72c0d14.webp?v=1767590510',
        'gallery': [
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/hero-xpulse-headlight-grill-lcb2_58980374-b92c-4f7d-9506-8e9bc72c0d14.webp?v=1767590510',
            'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/x-pulse-headlight-grill-lc-logo.jpg-3_52eb3ada-ca69-482d-872b-1567a4f56c5e.jpg?v=1767590510'
        ],
        'file_base': 'images_processed/catalog/lcb/lcb_x_pulse_headlight_grill'
    },

    # 10. X Pulse 200 4V Pro Defender Crashguard - ID 1459
    'hrz-lcb-x-pulse-200-4v-pro-defender-crashguard-1459': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/X1.jpg?v=1767590450',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/X1.jpg?v=1767590450'],
        'file_base': 'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_defender_crashguard_black'
    },

    # 11. X Pulse 200 4V Pro Vector Radiator Grill - ID 1469
    'hrz-lcb-x-pulse-200-4v-pro-vector-radiator-grill-1469': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_9b69a124-8d89-4721-b4e6-df41b2a30b7e.jpg?v=1767590415',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_9b69a124-8d89-4721-b4e6-df41b2a30b7e.jpg?v=1767590415'],
        'file_base': 'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_vector_radiator_grill'
    },

    # 12. X Pulse 200 4V Pro Tricorn Front Oil Cap - ID 1467
    'hrz-lcb-x-pulse-200-4v-pro-tricorn-front-oil-cap-1467': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_2625c8c1-2ab3-43c5-88ca-ccd7f9a3d163.jpg?v=1767590426',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_2625c8c1-2ab3-43c5-88ca-ccd7f9a3d163.jpg?v=1767590426'],
        'file_base': 'images_processed/catalog/lcb/lcb_x_pulse_200_4v_pro_tricorn_front_oil_cap'
    },

    # 13. Apache RTX 300 Raptor Crash Guard (Black) - ID 1426
    'hrz-lcb-tvs-apache-rtx-300-raptor-crash-guard-upper-lo-1426': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_4e00ee05-6657-4df2-8487-4bba3714600c.webp?v=1771825811',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_4e00ee05-6657-4df2-8487-4bba3714600c.webp?v=1771825811'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_raptor_crash_guard_upper_lower_s_black'
    },

    # 14. Apache RTX 300 Raptor Crash Guard (Red) - ID 1428
    'hrz-lcb-tvs-apache-rtx-300-raptor-crash-guard-upper-lo-1428': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_a7989ce6-e82c-4020-b1c0-2080eb59ca93.webp?v=1771595667',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/2_a7989ce6-e82c-4020-b1c0-2080eb59ca93.webp?v=1771595667'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_raptor_crash_guard_upper_lower_s_red'
    },

    # 15. Apache RTX 300 Raptor Crash Guard (White) - ID 1430
    'hrz-lcb-tvs-apache-rtx-300-raptor-crash-guard-upper-lo-1430': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_16f2391a-191c-4953-8b20-f8de056909a2.webp?v=1771495075',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_16f2391a-191c-4953-8b20-f8de056909a2.webp?v=1771495075'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_raptor_crash_guard_upper_lower_s'
    },

    # 16. Apache RTX 300 Titan Boot Guards - ID 1432
    'hrz-lcb-tvs-apache-rtx-300-titan-boot-guards-1432': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/bootgurd.webp?v=1771832902',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/bootgurd.webp?v=1771832902'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_titan_boot_guards'
    },

    # 17. Apache RTX 300 Tricorn Front Oil Cap - ID 1434
    'hrz-lcb-tvs-apache-rtx-300-tricorn-front-oil-cap-1434': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/CAP25806_03.jpg?v=1770968056',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/CAP25806_03.jpg?v=1770968056'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_tricorn_front_oil_cap'
    },

    # 18. Apache RTX 300 Bolster Pillion Footrest - ID 1418
    'hrz-lcb-tvs-apache-rtx-300-bolster-pillion-footrest-1418': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/FOO25816_02.jpg?v=1770967729',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/FOO25816_02.jpg?v=1770967729'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_bolster_pillion_footrest'
    },

    # 19. Apache RTX 300 Casque Rear Oil Cap - ID 1420
    'hrz-lcb-tvs-apache-rtx-300-casque-rear-oil-cap-1420': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/oil_cap_3d92ece8-f4fd-40a2-b242-53528dade1f5.webp?v=1771825949',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/oil_cap_3d92ece8-f4fd-40a2-b242-53528dade1f5.webp?v=1771825949'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_casque_rear_oil_cap'
    },

    # 20. Apache RTX 300 Genesis Side Stand Base - ID 1422
    'hrz-lcb-tvs-apache-rtx-300-genesis-side-stand-base-1422': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_80dc2a9d-f5a4-41ef-a9f4-500bc29a7193.jpg?v=1770885500',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/3_80dc2a9d-f5a4-41ef-a9f4-500bc29a7193.jpg?v=1770885500'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_genesis_side_stand_base'
    },

    # 21. Apache RTX 300 Ploigos GPS Mount - ID 1424
    'hrz-lcb-tvs-apache-rtx-300-ploigos-gps-mount-with-viso-1424': {
        'primary': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/MOB25817_01.jpg?v=1770967717',
        'gallery': ['https://cdn.shopify.com/s/files/1/0699/1354/2912/files/MOB25817_01.jpg?v=1770967717'],
        'file_base': 'images_processed/catalog/lcb/lcb_tvs_apache_rtx_300_ploigos_gps_mount_with_visor_ext'
    },
}

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

prod_by_id = {p['id']: p for p in products}

for pid, cfg in targets.items():
    if pid not in prod_by_id:
        print(f"WARNING: {pid} not found in products.json!")
        continue
    
    file_base = cfg['file_base']
    gallery_paths = []
    
    for idx, url in enumerate(cfg['gallery']):
        dest = f"{file_base}_{idx+1}.webp"
        download_and_process(url, dest)
        gallery_paths.append(dest)
        if idx == 0:
            # Also save base file
            download_and_process(url, f"{file_base}.webp")
            
    p = prod_by_id[pid]
    p['image'] = gallery_paths[0]
    p['gallery'] = gallery_paths
    print(f"Updated product {pid} -> {p['image']}")

with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

if os.path.exists('test design site/data/products.json'):
    with open('test design site/data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

print("\nSuccessfully updated data/products.json and test design site/data/products.json!")
