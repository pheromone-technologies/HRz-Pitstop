import os
import shutil
import sys

BASE_DIR = r"E:\coad\hrx website 2"
ARCHIVE_DIR = os.path.join(BASE_DIR, "_vault_archive")

PLAN = {
    "legacy_project_clones": [
        "hrx website 2",
        "hrx website 2.zip"
    ],
    "legacy_root_scripts": [
        "append_inventory.py",
        "append_inventory_fixed.py",
        "compress_images.py",
        "compress_videos.py",
        "compress_videos2.py",
        "download_ddgs_images.py",
        "expert_inventory_builder.py",
        "export_excel_to_json.py",
        "fetch_images.py",
        "fetch_logos.py",
        "fetch_wiki_images.py",
        "fill_blanks.py",
        "fill_blanks_v2.py",
        "final_verification.py",
        "fix_re.py",
        "fix_subcategories.py",
        "fix_subcategories_strict.py",
        "generate_sheet.py",
        "map_images.py",
        "match_script.py",
        "process_images.py",
        "update_app_js.py",
        "update_existing_sheet.py",
        "verify_ddgs.py"
    ],
    "scratch_and_tests": [
        "temp_old_app.js",
        "scratch_test.webp",
        "test_fitment.js",
        "test_render.html",
        "audit_log.json",
        "audit_names_review.csv",
        "manual_review_queue.csv",
        "matched_768_items.json",
        "staging.json",
        "sheet.csv",
        "verification_report.txt"
    ],
    "legacy_catalogs_and_workbooks": [
        "catalog.csv",
        "catalog.json",
        "Client_Hold_Generic_And_Unfound.xlsx",
        "HRZ_Pitstop_Client_Inventory_All_Bike_Models.xlsx",
        os.path.join("products data", "NA_Generic_Items_List_Current.xlsx"),
        os.path.join("products data", "Probable_Items_Current.xlsx"),
        os.path.join("products data", "Verified_Products_Current.xlsx")
    ],
    "scraper_working_cache": [
        "Needs_Scraping_Queue.csv",
        "scrape_manual_review.csv",
        "scraped_verified_results.json"
    ],
    "legacy_scripts": [
        os.path.join("scripts", "add_defer.py"),
        os.path.join("scripts", "audit_menu.js"),
        os.path.join("scripts", "audit_menu2.js"),
        os.path.join("scripts", "audit_menu3.js"),
        os.path.join("scripts", "audit_names.py"),
        os.path.join("scripts", "audit_scraped.py"),
        os.path.join("scripts", "consolidate_data.js"),
        os.path.join("scripts", "final_audit_check.py"),
        os.path.join("scripts", "follow_up.py"),
        os.path.join("scripts", "import_catalog.py"),
        os.path.join("scripts", "migrate_variants.py"),
        os.path.join("scripts", "pipeline.py"),
        os.path.join("scripts", "pipeline_stage2.py"),
        os.path.join("scripts", "run_all.py"),
        os.path.join("scripts", "test_recovery.py"),
        os.path.join("scripts", "update_menu_js.py")
    ]
}

def run_archive():
    print("=" * 65)
    print("HRZ PITSTOP: MOVING LEGACY & SCRATCH ARTIFACTS TO _vault_archive")
    print("=" * 65)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    total_moved = 0
    total_bytes = 0
    
    for folder_name, items in PLAN.items():
        dest_folder = os.path.join(ARCHIVE_DIR, folder_name)
        os.makedirs(dest_folder, exist_ok=True)
        print(f"\n[{folder_name}] -> _vault_archive/{folder_name}/")
        
        for item in items:
            src_path = os.path.join(BASE_DIR, item)
            if not os.path.exists(src_path):
                print(f"  - Skipped (not found): {item}")
                continue
            
            base_item_name = os.path.basename(item)
            dst_path = os.path.join(dest_folder, base_item_name)
            
            # Calculate size
            if os.path.isdir(src_path):
                sz = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(src_path) for fn in fns)
            else:
                sz = os.path.getsize(src_path)
            
            try:
                # If target already exists in archive, remove it first
                if os.path.exists(dst_path):
                    if os.path.isdir(dst_path):
                        shutil.rmtree(dst_path)
                    else:
                        os.remove(dst_path)
                
                shutil.move(src_path, dst_path)
                total_moved += 1
                total_bytes += sz
                print(f"  + Moved: {item} ({sz / 1024:.1f} KB)")
            except Exception as e:
                print(f"  ! Error moving {item}: {e}")
                
    print("\n" + "=" * 65)
    print(f"ARCHIVE COMPLETE: Successfully moved {total_moved} items ({total_bytes / 1024 / 1024:.2f} MB)")
    print("All items safely preserved in _vault_archive/")
    print("=" * 65)

if __name__ == "__main__":
    run_archive()
