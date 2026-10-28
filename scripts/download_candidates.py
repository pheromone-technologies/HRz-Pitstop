import urllib.request
import os
from PIL import Image

headers = {'User-Agent': 'Mozilla/5.0'}
os.makedirs('scratch/image_candidates', exist_ok=True)

urls = {
    # V Strom Crash Guard
    'vstrom_cg_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/11_d4c11087-735f-4523-bc7b-0fccd7676953.webp?v=1767593142',
    'vstrom_cg_2': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/CRA8478-legundary-v-strom-crashguard-with-slider2_1ff05a17-f79f-4fd9-8053-9462a2064314.webp?v=1767593142',
    'vstrom_cg_8': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/LCBVStromAdrinexCrashguardWithSlider.webp?v=1719981049',
    
    # V Strom Bashplate
    'vstrom_bp_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/14_65647fcb-ea3a-427e-982b-80ca9e68e2d3.webp?v=1767593106',
    'vstrom_bp_2': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG8482-LEGUNDARY-VSTROM-VAMBRACE-BASH-PLATE.webp?v=1767593106',
    'vstrom_bp_3': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG8482-LEGUNDARY-VSTROM-VAMBRACE-BASH-PLATE2.webp?v=1719979723',

    # Apache RTX Bashplate Silver
    'rtx_bp_silver_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG25818_02.jpg?v=1770967774',
    
    # Apache RTX Bashplate Black
    'rtx_bp_black_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/bash.webp?v=1771827830',
    'rtx_bp_black_2': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/ENG25818_01.jpg?v=1771827830',
    
    # Apache RTX Radiator Grill Black
    'rtx_rad_black_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/reditor_22.webp?v=1771828206',
    'rtx_rad_black_2': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_aa3c2f73-f84b-481b-939f-c38a9bda2f07.jpg?v=1771828206',

    # Apache RTX Radiator Grill Silver
    'rtx_rad_silver_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/RAG25809_03.jpg?v=1770967982',
    'rtx_rad_silver_2': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/WEBSIZEcopy.jpg?v=1770967982',

    # XPulse Cosmic Headlight Grill
    'xpulse_cosmic_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_116d4824-e0a3-403b-a5fb-989a4ecfb901.jpg?v=1767590437',
    'xpulse_cosmic_2': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/1_23382af5-ea93-469c-9ee9-75dc82ca1a59.jpg?v=1767590437',

    # XPulse Headlight Grill
    'xpulse_hl_1': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/x-pulse-headlight-grill-lc-logo.jpg-3_52eb3ada-ca69-482d-872b-1567a4f56c5e.jpg?v=1767590510',
    'xpulse_hl_2': 'https://cdn.shopify.com/s/files/1/0699/1354/2912/files/hero-xpulse-headlight-grill-lcb2_58980374-b92c-4f7d-9506-8e9bc72c0d14.webp?v=1767590510',
}

for name, url in urls.items():
    ext = '.webp' if '.webp' in url else '.jpg'
    dest = f"scratch/image_candidates/{name}{ext}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp, open(dest, 'wb') as f:
            f.write(resp.read())
        im = Image.open(dest)
        print(f"Downloaded {name}: size={im.size}, mode={im.mode}")
    except Exception as e:
        print(f"Failed {name}: {e}")
