#!/usr/bin/env python3
"""
HRz Pitstop: Rebuild & Sync Perfect Product Images
Eliminates rough edges, black cutout halos, and vendor logo placeholders.
Standardizes on 1000x1000 pure white canvas with subtle padding and HRZ logo.
Syncs data/products.json, test design site/data/products.json, and Final_Master_Catalogue_VERIFIED.xlsx.
"""

import os
import sys
import json
import shutil
from PIL import Image
import openpyxl

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\coad\hrx website 2"
LOGO_FILE = r"E:\coad\tools for hrz\image logo editor\HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.png"
PRODUCTS_JSON = os.path.join(BASE_DIR, "data", "products.json")
TEST_PRODUCTS_JSON = os.path.join(BASE_DIR, "test design site", "data", "products.json")
EXCEL_FILE = os.path.join(BASE_DIR, "Final_Master_Catalogue_VERIFIED.xlsx")

if not os.path.exists(LOGO_FILE):
    print(f"ERROR: Logo file not found at {LOGO_FILE}")
    sys.exit(1)

HRZ_LOGO = Image.open(LOGO_FILE).convert('RGBA')

REBUILD_MAP = {
    # 1. Givi top cases (Screenshot 1)
    'images_processed/catalog/givi/givi_matterhorn_aluminium_top_case_47ltrs_plate_chr_mtn_1.webp':
        'images_processed/scraped/givi/Givi_Matterhorn_Aluminium_Top_Case_47ltrs_Pla_880387.webp',
    'images_processed/catalog/givi/givi-43ltr_mulebox_monolock_topcaseblk_tech_e43ntl_2.webp':
        'images_processed/scraped/givi/Givi-43ltr_Mulebox_Monolock_TopcaseBlk_Tech_E_711785.webp',
        
    # 2. Carbonado Quench Bladder (Screenshot 2)
    'images_processed/catalog/carbonado/carbonado_quench_hydration_bladder_2_5l_1.webp':
        'images_processed/scraped/carbonado/CARBONADO_QUENCH_HYDRATION_BLADDER_2_5L_260657.webp',
        
    # 3. Carbonado Y07 Hydration Backpack (Screenshot 4 - Auto Warrior logo)
    'images_processed/catalog/carbonado/carbonado_y07_ultimate_hydration_back_pack_blue_7_lts_c.webp':
        'images/carbonado/carbonado_y07_backpack.webp',
        
    # 4. Ogio Backpack (Autonity "A" logo)
    'images_processed/catalog/ogio/ogio_back_pack.webp':
        'images/ogio/ogio_backpack.webp',
    'images/dsg/Back.webp':
        'images/ogio/ogio_backpack.webp',

    # 5. Norifumi Noctus Exhaust (Autonity "A" logo)
    'images_processed/catalog/norifumi/norifumi_noctus_t5_crf_150l_db.webp':
        'images_processed/scraped/generic_unbranded/NORIFUMI_N4_CRF_150L-DB_L_917707.webp',
    'images/vega/150.webp':
        'images_processed/scraped/generic_unbranded/NORIFUMI_N4_CRF_150L-DB_L_917707.webp',

    # 6. Apollo Tyres (Apollo company logo)
    'images_processed/catalog/apollo/apollo_90_90-21_54h_tramplr_xr_tl.webp':
        'images/apollo/apollo_tramplr_xr.webp',

    # 7. 66BHP Products (66BHP company logo)
    'images_processed/catalog/66_bhp/66_bhp_hand_sleeve.webp':
        'images/66_bhp/66_bhp_hand_sleeve.webp',
    'images_processed/catalog/66_bhp/66_bhp_chain_lub.webp':
        'images_processed/scraped/motul/M-CHAIN_LUBE_ROAD-400ML-595_800463.webp',
    'images_processed/catalog/66_bhp/66bhp-micro_fiber_cloth_250gsm_red.webp':
        'images_processed/scraped/lgp/LGP_MICRO_FIBER_CLOTH_400_GSM_804965.webp',

    # 8. Axor Rider Jacket Drift (BKWGears logo)
    'images_processed/catalog/axor/axor_rider_jacket_drift.webp':
        'images/scala/ScalaBlazeRidingJacket-BlackandNeonFrontView.webp',

    # 9. Vega Balaclava (BKWGears logo)
    'images_processed/catalog/vega/vega_balclavaa.webp':
        'images/vega/BalaclavaHeadProtection.webp',

    # 10. Lever Guard BSDDP (Ride Adventure logo)
    'images_processed/catalog/bsddp/lever_guard_bsddp_adj.webp':
        'images_processed/scraped/bsddp/BSDDP_LEVER_GUARD_CARBON_METAL_BLACK_704099.webp',

    # 11. MT Triumph Footrest (OpenRoad logo)
    'images_processed/catalog/moto_torque/mt-_triumph_foot_rest.webp':
        'images/legundary_customs/FOO16454LCBTRIUMPHTIGER660BLOSTERPILLIONFOOTREST.webp',

    # 12. Studds Helmets (Studds banner & IndiaMart logo)
    'images_processed/catalog/studds/studds_f_f_drifter_decor.webp':
        'images/studds/DRIFTER-BLACK-matt-0-1.webp',
    'images_processed/catalog/studds/studds_f_f_driftter_decor.webp':
        'images/studds/DRIFTER-BLACK-matt-0-1.webp',
    'images_processed/catalog/studds/studds_f_f_raider_super_decor.webp':
        'images_processed/scraped/studds/STUDDS_RAIDER_STREET_BK_L_345894.webp',

    # 13. SMK Outer Visor (Bikester Global logo)
    'images_processed/catalog/smk/smk_outer_visor_stellar_clear_tinted.webp':
        'images_processed/scraped/smk/SMK_OUTER_VISOR_STELLAR_MIRROR_RAINBOW_259110.webp',

    # 14. ViaTerra Saddle Bag (ViaTerra logo)
    'images_processed/catalog/viaterra/viaterra_-_100_wp_leh_saddle_bag.webp':
        'images/saddlebags_product.webp',

    # 15. Tryka Helmet Bag (Tryka logo)
    'images_processed/catalog/tryka_gears/tryka-helmet_bag.webp':
        'images_processed/scraped/carbonado/Carbonado-_Discovery_Helmet_Bag_Large_937753.webp',

    # 16. LCB Crashguards & Accessories (MotoModz logo)
    'images_processed/catalog/lcb/lcb_adv390_bellator_lower_crashguard_black.webp':
        'images/legundary_customs/advlowercrashguard.webp',
    'images_processed/catalog/lcb/lcb_adv390_raptor_upper_crashguard_black.webp':
        'images/legundary_customs/CRA17389bmwg310gsraptoruppercrashguard_2d200189-9d29-46fd-a463-da8e2a60d6b9.webp',
    'images_processed/catalog/lcb/lcb_adv390_raptor_upper_crashguard_black_2025.webp':
        'images/legundary_customs/CRA17389bmwg310gsraptoruppercrashguard_2d200189-9d29-46fd-a463-da8e2a60d6b9.webp',
    'images_processed/catalog/lcb/lcb_himalayan_rear_break_fluid_cap_ss.webp':
        'images_processed/scraped/lcb/LCB_HIMALAYAN_450_CASQUE_REAR_BRAKE_FLUID_CAP_087971.webp',
    'images_processed/catalog/lcb/lcb_himalayan_rear_brake_fluid_cap_ss.webp':
        'images_processed/scraped/lcb/LCB_HIMALAYAN_450_CASQUE_REAR_BRAKE_FLUID_CAP_087971.webp',
    'images_processed/catalog/lcb/lcb_hness_spyro_rear_break_fluid_cap.webp':
        'images_processed/scraped/lcb/LCB_CB200x_Spyro_Rear_Brake_Fluid_Cap_392303.webp',
    'images/vega/4.webp':
        'images/legundary_customs/FOO17860LCBREGUERRILLA450BOLSTERPILLIONFOOTREST.webp',
    'images_processed/catalog/lcb/lcb_himalaya_450_bolide_pillion_footrest.webp':
        'images/legundary_customs/FOO17860LCBREGUERRILLA450BOLSTERPILLIONFOOTREST.webp',

    # 17. KYT TT REVO Helmets (Shop header banners)
    'images_processed/catalog/kyt/tt_revo_flux_m.webp':
        'images/kyt/02asphaltgrey-fluxia1.webp',
    'images_processed/catalog/kyt/tt_revo_gear_black_red_m.webp':
        'images/kyt/02mattblackred1.webp',
    'images_processed/catalog/kyt/tt_revo_grand_prix_white_light_blue_l.webp':
        'images/kyt/Y6TR0051_KYT_TT_REVO_SPEEDING_WHITE_RED_1.webp',
    'images_processed/catalog/kyt/tt_revo_leopard_india_edition_l.webp':
        'images/kyt/capacete-kyt-nf-j-dennis-foggia-leopard-replica-63e52417ad74d.webp',
    'images_processed/catalog/kyt/tt_revo_overtech_black_orange_m.webp':
        'images/kyt/Y6TRX042-KYTTT-REVOOVERTECHBLACKFUXIA.webp',
    'images_processed/catalog/kyt/tt_revo_sushi_time_l.webp':
        'images/kyt/Y6TR0042-KYTTT-REVOSUSHITIME_1.webp',
    'images_processed/catalog/kyt/tt_revo_tourist_red_fluo_l.webp':
        'images/kyt/Y6TRX0W7D-KYT-TTREVO-PLAINGARARED_1.webp',

    # 18. SMK Helmets
    'images_processed/catalog/smk/smk_typhoon_sparko_gl266_l.webp':
        'images_processed/scraped/smk/SMK_TYPHOON_AFROT_GL266_L_135677.webp',
    'images/raida/2.webp':
        'images_processed/scraped/smk/SMK_TYPHOON_AFROT_GL266_L_135677.webp',
    'images_processed/catalog/smk/smk_stellar_sports_flight_gl213_l.webp':
        'images_processed/smk/STELLAR-SPORT-FLIGHT-GL-213-1.webp',

    # 19. Black Background Products (Halos / Edge artifacts)
    'images_processed/catalog/cramster/cramster_stallion_saddle_bag_-_black_-_60l_1.webp':
        'images/cramster/Cramster_Colt2Saddlebag52L_001_2.webp',
    'images_processed/catalog/lcb/lcb_triumph_speed_400_carrier_plate_1.webp':
        'images_processed/scraped/lcb/LCB_TRIUMPH_SPEED_400_CARRIER_PLATE_415690.webp',
    'images_processed/catalog/moto_torque/mt_-_honda_h_ness_350_back_carrier_1.webp':
        'images_processed/scraped/moto_torque/MT_-_HONDA_CB_350_RS_BACK_CARRIER_324493.webp',
    'images_processed/catalog/moto_torque/mt_-_honda_h_ness_350_engine_gaurd_1.webp':
        'images_processed/scraped/moto_torque/MT_-_HONDA_H_NESS_350_ENGINE_GAURD_345331.webp',
    'images_processed/catalog/lcb/lcb_yamaha_xsr_155_aero_short_visor_blk_silver.webp':
        'images_processed/scraped/lcb/LCB_YAMAHA_XSR_155_ZEPHYR_VISOR_BLK_SILVER_790584.webp',
    'images_processed/catalog/red_rooster_performance/rrp_rumbler_ace_exhaust_unibody_black_2.webp':
        'images_processed/scraped/red_rooster_performance/RRP_RUMBLER_ACE_EXHAUST_UNIBODY_BLACK_695007.webp',
    'images_processed/catalog/jawa/flash_x_jawa_42.webp':
        'images_processed/scraped/jawa/FLASH_X_JAWA_42_320085.webp',
    'images_processed/catalog/flash_x/flash_x_scram_411.webp':
        'images_processed/scraped/flash_x/FLASH_X_SCRAM_411_369877.webp',
    'images_processed/catalog/yamaha/flash_x_hazard_yamaha_fzs.webp':
        'images_processed/scraped/yamaha/FLASH_X_HAZARD_YAMAHA_MT_15_911686.webp',
    'images_processed/catalog/ktm/flash_x_hazard_ktm_duke_200_bs6_4.webp':
        'images_processed/scraped/ktm/FLASH_X_HAZARD_KTM_DUKE_200_BS6_067757.webp',
    'images_processed/catalog/scala_gears/scala_kneeguard.webp':
        'images/axor_helmets/IMPACT-XKNEEGUARD4.webp',
    'images_processed/catalog/moto_torque/mt_-_him_450_rear_master_cyl_guard_ss.webp':
        'images/legundary_customs/himalayan-master-cylinder-guard-black2.webp',
    'images_processed/catalog/moto_torque/mt_-_himalayan_450_front_master_cylinder_guard_black.webp':
        'images/legundary_customs/himalayan-master-cylinder-guard-black2.webp',
    'images_processed/catalog/moto_torque/mt_-_him_450_handlebar_risers.webp':
        'images/mototorque/HANDLE-BAR-RISERS-ALUMINIUM.webp',
    'images_processed/catalog/moto_torque/mt_-_him_450_gps_mount.webp':
        'images_processed/scraped/moto_torque/MOTO_TORQUE_HIMALAYA_GPS_MOUNT_261070.webp',
    'images_processed/catalog/moto_torque/mt_-_himalayan_450_-_gps_mount.webp':
        'images_processed/scraped/moto_torque/MOTO_TORQUE_HIMALAYA_GPS_MOUNT_261070.webp',
    'images_processed/catalog/moto_torque/mt_-_himalayan_gps_mount.webp':
        'images_processed/scraped/moto_torque/MOTO_TORQUE_HIMALAYA_GPS_MOUNT_261070.webp',
    'images_processed/catalog/moto_torque/mt_-_pulsar_ns_200_crash_guard.webp':
        'images/legundary_customs/cb200x-crashguard-CRA66942.webp',
    'images_processed/catalog/moto_torque/mt-himalayan_450_radiator_guard-black.webp':
        'images/mototorque/kawasakiRESERVOIROILGUARD_b556b461-7a74-4b89-b844-4c9bf198c44d.webp',
    'images_processed/catalog/moto_torque/mt-himalayan_450_reservoir_oil_guard_black.webp':
        'images/mototorque/RESERVOIR-OIL-GUARD-1.webp'
}

def render_standard_product_image(src_rel, dest_rel):
    src_full = os.path.join(BASE_DIR, src_rel.replace('/', os.sep))
    dest_full = os.path.join(BASE_DIR, dest_rel.replace('/', os.sep))
    
    if not os.path.exists(src_full):
        print(f"  [SKIP] Source missing: {src_rel}")
        return False
        
    os.makedirs(os.path.dirname(dest_full), exist_ok=True)
    
    try:
        src_img = Image.open(src_full).convert('RGBA')
        CANVAS_SIZE = 1000
        canvas = Image.new('RGBA', (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255, 255))
        
        # Scale product comfortably inside 860x860
        MAX_INNER = 860
        w, h = src_img.size
        scale = min(MAX_INNER / w, MAX_INNER / h)
        new_w = max(10, int(w * scale))
        new_h = max(10, int(h * scale))
        
        resized_prod = src_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        pos_x = (CANVAS_SIZE - new_w) // 2
        pos_y = (CANVAS_SIZE - new_h) // 2
        
        canvas.alpha_composite(resized_prod, dest=(pos_x, pos_y))
        
        # Stamp HRZ logo in bottom right
        wm_w = 90
        wm_ratio = wm_w / float(HRZ_LOGO.width)
        wm_h = int(HRZ_LOGO.height * wm_ratio)
        resized_logo = HRZ_LOGO.resize((wm_w, wm_h), Image.Resampling.LANCZOS)
        
        logo_x = CANVAS_SIZE - wm_w - 24
        logo_y = CANVAS_SIZE - wm_h - 24
        canvas.alpha_composite(resized_logo, dest=(logo_x, logo_y))
        
        final_rgb = canvas.convert('RGB')
        final_rgb.save(dest_full, 'WEBP', quality=92)
        print(f"  [OK] Rendered: {dest_rel}")
        return True
    except Exception as e:
        print(f"  [ERROR] {dest_rel}: {e}")
        return False

print("=" * 70)
print("REBUILDING PRODUCT IMAGES")
print(f"Total targets: {len(REBUILD_MAP)}")
print("=" * 70)

success = 0
for dest, src in REBUILD_MAP.items():
    if render_standard_product_image(src, dest):
        success += 1

print(f"\nRendered {success}/{len(REBUILD_MAP)} images successfully!")

# Now synchronize data/products.json and test design site/data/products.json
print("\n" + "=" * 70)
print("UPDATING PRODUCT METADATA IN JSON STOREFRONTS")
print("=" * 70)

with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
    products = json.load(f)

# Name-based overrides to ensure clean image & gallery
PRODUCT_OVERRIDES = {
    'CARBONADO Y07 ULTIMATE HYDRATION BACK PACK BLUE (7 LTS CAPACITY)': {
        'image': 'images_processed/catalog/carbonado/carbonado_y07_ultimate_hydration_back_pack_blue_7_lts_c.webp',
        'gallery': ['images_processed/catalog/carbonado/carbonado_y07_ultimate_hydration_back_pack_blue_7_lts_c.webp']
    },
    'OGIO BACK PACK': {
        'image': 'images_processed/catalog/ogio/ogio_back_pack.webp',
        'gallery': ['images_processed/catalog/ogio/ogio_back_pack.webp', 'images/dsg/Back.webp']
    },
    'NORIFUMI NOCTUS T5 CRF 150L +DB': {
        'image': 'images_processed/catalog/norifumi/norifumi_noctus_t5_crf_150l_db.webp',
        'gallery': ['images_processed/catalog/norifumi/norifumi_noctus_t5_crf_150l_db.webp']
    },
    'APOLLO 90/90-21 54H TRAMPLR XR TL': {
        'image': 'images_processed/catalog/apollo/apollo_90_90-21_54h_tramplr_xr_tl.webp',
        'gallery': ['images_processed/catalog/apollo/apollo_90_90-21_54h_tramplr_xr_tl.webp']
    },
    '66 BHP HAND SLEEVE': {
        'image': 'images_processed/catalog/66_bhp/66_bhp_hand_sleeve.webp',
        'gallery': ['images_processed/catalog/66_bhp/66_bhp_hand_sleeve.webp']
    },
    '66 BHP CHAIN LUB': {
        'image': 'images_processed/catalog/66_bhp/66_bhp_chain_lub.webp',
        'gallery': ['images_processed/catalog/66_bhp/66_bhp_chain_lub.webp']
    },
    '66BHP-MICRO FIBER CLOTH 250GSM RED': {
        'image': 'images_processed/catalog/66_bhp/66bhp-micro_fiber_cloth_250gsm_red.webp',
        'gallery': ['images_processed/catalog/66_bhp/66bhp-micro_fiber_cloth_250gsm_red.webp']
    },
    'CARBONADO QUENCH HYDRATION BLADDER 2.5L': {
        'image': 'images_processed/catalog/carbonado/carbonado_quench_hydration_bladder_2_5l_1.webp',
        'gallery': [
            'images_processed/catalog/carbonado/carbonado_quench_hydration_bladder_2_5l_1.webp',
            'images/cramster/Quench_Hydration_Bladder_3D_Images_Website_1_jpg.webp',
            'images/cramster/Quench_Hydration_Bladder_3D_Images_Website_2_jpg.webp'
        ]
    },
    'Givi Matterhorn Aluminium Top Case 47ltrs Plate Chr (MTN47A(WP))': {
        'image': 'images_processed/catalog/givi/givi_matterhorn_aluminium_top_case_47ltrs_plate_chr_mtn_1.webp',
        'gallery': ['images_processed/catalog/givi/givi_matterhorn_aluminium_top_case_47ltrs_plate_chr_mtn_1.webp']
    },
    'Givi-43ltr Mulebox Monolock TopcaseBlk (Tech) ( E43NTL)': {
        'image': 'images_processed/catalog/givi/givi-43ltr_mulebox_monolock_topcaseblk_tech_e43ntl_2.webp',
        'gallery': ['images_processed/catalog/givi/givi-43ltr_mulebox_monolock_topcaseblk_tech_e43ntl_2.webp']
    },
    'SMK TYPHOON SPARKO GL266': {
        'image': 'images_processed/catalog/smk/smk_typhoon_sparko_gl266_l.webp',
        'gallery': ['images_processed/catalog/smk/smk_typhoon_sparko_gl266_l.webp']
    },
    'LCB HIMALAYA 450 BOLIDE PILLION FOOTREST': {
        'image': 'images_processed/catalog/lcb/lcb_himalaya_450_bolide_pillion_footrest.webp',
        'gallery': ['images_processed/catalog/lcb/lcb_himalaya_450_bolide_pillion_footrest.webp']
    },
    'LCB HNESS SPYRO REAR BREAK FLUID CAP': {
        'image': 'images_processed/catalog/lcb/lcb_hness_spyro_rear_break_fluid_cap.webp',
        'gallery': ['images_processed/catalog/lcb/lcb_hness_spyro_rear_break_fluid_cap.webp']
    }
}

updated_count = 0
for p in products:
    pname = p.get('name', '')
    if pname in PRODUCT_OVERRIDES:
        p.update(PRODUCT_OVERRIDES[pname])
        updated_count += 1

print(f"Updated {updated_count} storefront product overrides in memory.")

with open(PRODUCTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
print(f"Saved: {PRODUCTS_JSON}")

with open(TEST_PRODUCTS_JSON, 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)
print(f"Saved: {TEST_PRODUCTS_JSON}")

# Sync to Excel
print("\n" + "=" * 70)
print("UPDATING FINAL MASTER CATALOGUE EXCEL")
print("=" * 70)

wb = openpyxl.load_workbook(EXCEL_FILE)
ws = wb.active
headers = [str(cell.value or '').strip() for cell in ws[1]]
name_col = headers.index('Product Name') + 1
img_col = headers.index('Product Image Filename / URL') + 1

excel_updates = 0
for row in range(2, ws.max_row + 1):
    row_name = str(ws.cell(row=row, column=name_col).value or '').strip()
    if row_name in PRODUCT_OVERRIDES:
        ws.cell(row=row, column=img_col, value=PRODUCT_OVERRIDES[row_name]['image'])
        excel_updates += 1

wb.save(EXCEL_FILE)
print(f"Updated {excel_updates} rows in {EXCEL_FILE}")
print("ALL TASKS COMPLETED SUCCESSFULLY!")
