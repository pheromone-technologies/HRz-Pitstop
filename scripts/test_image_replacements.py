import json
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/bad_images_summary.json', encoding='utf-8') as f:
    bad_items = json.load(f)

print(f"Total bad items in summary: {len(bad_items)}")

# Manual precise mapping for known tricky items
EXACT_REPLACEMENTS = {
    # Gator gloves
    'images_processed/catalog/axor/axor_gator_gloves_black_grey_m.webp': 'images_processed/inventory_sync_fuzzy/axor/GatorBLK-Red2.webp',
    'images_processed/catalog/axor/axor_gator_gloves_black_grey_xl.webp': 'images_processed/inventory_sync_fuzzy/axor/GatorBLK-Red2.webp',
    'images_processed/catalog/axor/axor_gator_gloves_black_neon_green_l.webp': 'images_processed/inventory_sync_fuzzy/axor/Gator_Black_Neon_Green_1_765x_a62a8194-93dd-4ef9-ae96-20b37612d7b6.webp',
    'images_processed/catalog/axor/axor_gator_gloves_black_neon_green_m.webp': 'images_processed/inventory_sync_fuzzy/axor/Gator_Black_Neon_Green_1_765x_a62a8194-93dd-4ef9-ae96-20b37612d7b6.webp',
    'images_processed/catalog/axor/axor_gator_gloves_black_neon_green_xl.webp': 'images_processed/inventory_sync_fuzzy/axor/Gator_Black_Neon_Green_1_765x_a62a8194-93dd-4ef9-ae96-20b37612d7b6.webp',
    'images_processed/catalog/axor/axor_gator_gloves_black_red_l.webp': 'images_processed/inventory_sync_multisite/axor/Gator_Black_Red_1_765x_44663151-1aed-4b04-82b4-396c6517bb09.webp',
    'images_processed/catalog/axor/axor_gator_gloves_black_red_m.webp': 'images_processed/inventory_sync_multisite/axor/Gator_Black_Red_1_765x_44663151-1aed-4b04-82b4-396c6517bb09.webp',
    'images_processed/catalog/axor/axor_gator_gloves_black_red_xl.webp': 'images_processed/inventory_sync_multisite/axor/Gator_Black_Red_1_765x_44663151-1aed-4b04-82b4-396c6517bb09.webp',
    'images_processed/catalog/axor/axor_gloves_gator.webp': 'images_processed/inventory_sync_multisite/axor/Gator_Black_Red_1_765x_44663151-1aed-4b04-82b4-396c6517bb09.webp',
    
    # Throttle clean
    'images_processed/catalog/motul/m-throttle_body_clean-100ml-200.webp': 'images_processed/scraped/motul/M-THROTTLE_BODY_CLEAN-100ML-200_302653.webp',
    
    # Fog light & mounts
    'images_processed/catalog/lgp/lgp_fog_lamp_dk16.webp': 'images_processed/scraped/lgp/LGP_SPOT_LIGHT_FOG_LIGHT_DK40_4_LED_50W_928742.webp',
    'images_processed/catalog/moto_torque/moto_torque_guerrilla_h_grill.webp': 'images_processed/scraped/generic_unbranded/FOG_LIGHT_MOUNT_FIT0039_997660.webp',
    'images_processed/catalog/moto_torque/mt_-_scram_411_fog_light_mount.webp': 'images_processed/scraped/moto_torque/MT_-_HARLEY_DAVIDSON_440X_FOGLIGHT_MOUNT_841665.webp',
    
    # Helmets
    'images_processed/catalog/smk/smk_stellar_sports_flight_gl213_l.webp': 'images_processed/smk/STELLAR-SPORT-FLIGHT-GL-213-1.webp',
    'images_processed/catalog/smk/smk_stellar_sports_fury_gl257_l.webp': 'images_processed/smk/STELLAR-FURY-GL-257C-1.webp',
    'images_processed/catalog/smk/smk_agnar_w_cv_cyborg_gl266_xl_pf_1.webp': 'images_processed/smk/STELLAR-2.webp',
    'images_processed/catalog/studds/studds_f_f_raider_super_decor.webp': 'images_processed/scraped/studds/STUDDS_RAIDER_STREET_BK_L_345894.webp',
    'images_processed/catalog/unbranded/sbh-61_d_v_sxe_afs_sp3_matt_blk_blue_helmet_580mm_sbhg6.webp': 'images_processed/scraped/steelbird/SBH-61_D_V_SXE_AFS_EDITION_MATT_BLK_HELMET_58_441921.webp',
    'images_processed/catalog/unbranded/sbh-61_d_v_sxe_afs_sp3_glsy_blk_blue_helmet_600mm_sbh61.webp': 'images_processed/scraped/steelbird/SBH-61_D_V_SXE_AFS_EDITION_GLSY_BLK_HELMET_60_441921.webp',
    
    # Scala gear
    'images_processed/catalog/scala_gears/scala_rain_pant.webp': 'images_processed/scala/Designed_for_touring_enthusiasts_as_well_as_everyday_commuters_the_Scala_Hydra_Seal_Rain_Pant_delivers_dependable_waterproof_protection_enhanced_visibility_and_lasting_comfort_on_ever.webp',
    'images_processed/catalog/scala_gears/scala_boots.webp': 'images_processed/catalog/raida/raida_-_drymax_rain_pant_size_xl.webp',
    'images_processed/catalog/scala_gears/scala_air_gloves.webp': 'images_processed/scraped/lgp/GLOVES_LGP_265872.webp',
    
    # Sliders & protection
    'images_processed/catalog/bmw/rear_fork_sliders_bmw-310.webp': 'images_processed/mototorque/fork-sliders.webp',
    
    # Tyres
    'images_processed/catalog/apollo/apollo_90_90-21_54h_tramplr_xr_tl.webp': 'images_processed/catalog/apollo/apollo_110_90-18_61p_actigrip_r4_tt.webp',
    
    # C5 paste & Ez lube
    'images_processed/catalog/motul/c5_chain_paste_-150_ml_pcs.webp': 'images_processed/catalog/motul/m-chain_clean_400ml-535.webp',
    'images_processed/catalog/motul/m-ez_lube_-400ml-380.webp': 'images_processed/catalog/motul/m-chain_clean_400ml-535.webp'
}

for pid, info in bad_items.items():
    orig_path = info['path'].replace('\\', '/')
    if orig_path in EXACT_REPLACEMENTS:
        rep = EXACT_REPLACEMENTS[orig_path]
        print(f"MATCH (Exact): {info['name']} -> {rep}")
    else:
        # Search scraped or processed
        base = os.path.basename(orig_path).replace('.webp', '')
        cands = []
        for root, dirs, files in os.walk('images_processed'):
            if 'catalog' in root: continue
            for f in files:
                f_path = os.path.join(root, f).replace('\\', '/')
                f_low = f.lower()
                if (base in f_low or any(w in f_low for w in info['name'].lower().split() if len(w) > 4)) and os.path.getsize(f_path) > 10000:
                    cands.append(f_path)
        if cands:
            print(f"MATCH (Auto):  {info['name']} -> {cands[0]} (out of {len(cands)})")
        else:
            print(f"MISSING:       {info['name']} ({orig_path})")
