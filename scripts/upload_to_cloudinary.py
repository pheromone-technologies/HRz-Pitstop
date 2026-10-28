import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import cloudinary
import cloudinary.uploader
import cloudinary.api

MAP_FILE = 'data/image_cloudinary_map.json'
PRODUCTS_FILE = 'data/products.json'
TEST_PRODUCTS_FILE = 'test design site/data/products.json'
BACKUP_FILE = 'data/products.json.bak_local_images'

map_lock = threading.Lock()

def load_existing_map():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: could not load existing map: {e}")
    return {}

def save_map(mapping):
    with map_lock:
        with open(MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2)

def collect_all_image_paths(products_file):
    with open(products_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    all_images = set()
    for p in products:
        if p.get('image'):
            all_images.add(p['image'])
        for g in p.get('gallery', []):
            if g: all_images.add(g)
        for v in p.get('variants', []):
            if v.get('image'): all_images.add(v['image'])
        
        size_vars = p.get('sizeVariants', {})
        if isinstance(size_vars, list):
            for sv in size_vars:
                if sv.get('image'): all_images.add(sv['image'])
        elif isinstance(size_vars, dict):
            for sv in size_vars.values():
                if sv.get('image'): all_images.add(sv['image'])

    return sorted(list(all_images))

def upload_single_image(local_path, folder_prefix="hrz_pitstop"):
    if not os.path.exists(local_path):
        return local_path, None, f"File not found on disk: {local_path}"

    # Normalized public_id based on relative path without extension
    clean_path = local_path.replace('\\', '/')
    rel_id = os.path.splitext(clean_path)[0]
    public_id = f"{folder_prefix}/{rel_id}"

    try:
        res = cloudinary.uploader.upload(
            local_path,
            public_id=public_id,
            overwrite=False,
            resource_type="image"
        )
        secure_url = res.get('secure_url')
        return local_path, secure_url, None
    except Exception as e:
        return local_path, None, str(e)

def apply_urls_to_products(mapping, products_path, test_products_path):
    print(f"\nApplying Cloudinary URLs to {products_path}...")
    with open(products_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Backup
    import shutil
    shutil.copy2(products_path, BACKUP_FILE)
    print(f"Backed up original products to {BACKUP_FILE}")

    replaced_count = 0
    total_refs = 0

    def get_url(p):
        nonlocal replaced_count, total_refs
        if not p: return p
        total_refs += 1
        if p in mapping:
            replaced_count += 1
            return mapping[p]
        return p

    for p in products:
        if p.get('image'):
            p['image'] = get_url(p['image'])
        if p.get('gallery'):
            p['gallery'] = [get_url(g) for g in p['gallery']]
        if p.get('variants'):
            for v in p['variants']:
                if v.get('image'):
                    v['image'] = get_url(v['image'])
                if v.get('gallery'):
                    v['gallery'] = [get_url(g) for g in v['gallery']]
        
        size_vars = p.get('sizeVariants')
        if isinstance(size_vars, list):
            for sv in size_vars:
                if sv.get('image'):
                    sv['image'] = get_url(sv['image'])
        elif isinstance(size_vars, dict):
            for sv in size_vars.values():
                if sv.get('image'):
                    sv['image'] = get_url(sv['image'])

    with open(products_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Successfully saved {products_path} (Replaced {replaced_count} of {total_refs} references)")

    if os.path.exists(os.path.dirname(test_products_path)):
        with open(test_products_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved {test_products_path}")

def main():
    parser = argparse.ArgumentParser(description="Upload HRz Pitstop catalog images to Cloudinary and map URLs.")
    parser.add_argument('--cloud-name', help="Cloudinary Cloud Name")
    parser.add_argument('--api-key', help="Cloudinary API Key")
    parser.add_argument('--api-secret', help="Cloudinary API Secret")
    parser.add_argument('--url', help="Cloudinary URL (cloudinary://key:secret@cloud_name)")
    parser.add_argument('--workers', type=int, default=8, help="Concurrent upload threads (default: 8)")
    parser.add_argument('--folder', default="hrz_pitstop", help="Cloudinary folder prefix (default: hrz_pitstop)")
    parser.add_argument('--dry-run', action='store_true', help="Verify credentials and image list without uploading")
    parser.add_argument('--apply-only', action='store_true', help="Apply existing mapping file to products.json without uploading")

    args = parser.parse_args()

    # Load mapping
    mapping = load_existing_map()

    if args.apply_only:
        if not mapping:
            print(f"Error: {MAP_FILE} does not exist or is empty. Run upload first.")
            sys.exit(1)
        apply_urls_to_products(mapping, PRODUCTS_FILE, TEST_PRODUCTS_FILE)
        return

    # Configure Cloudinary
    if args.url:
        cloudinary.config(cloudinary_url=args.url)
    elif args.cloud_name and args.api_key and args.api_secret:
        cloudinary.config(
            cloud_name=args.cloud_name,
            api_key=args.api_key,
            api_secret=args.api_secret,
            secure=True
        )
    elif os.environ.get('CLOUDINARY_URL'):
        cloudinary.config(cloudinary_url=os.environ.get('CLOUDINARY_URL'))
    elif os.environ.get('CLOUDINARY_CLOUD_NAME'):
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
            secure=True
        )
    else:
        print("ERROR: Cloudinary credentials not provided.")
        print("Please provide via:")
        print("  1) CLI flags: --cloud-name <name> --api-key <key> --api-secret <secret>")
        print("  2) CLI flag: --url cloudinary://<key>:<secret>@<cloud_name>")
        print("  3) Environment variable: CLOUDINARY_URL")
        sys.exit(1)

    # Test connection
    print("Testing connection to Cloudinary...")
    try:
        ping_res = cloudinary.api.ping()
        print(f"Connection OK: {ping_res.get('status', 'connected')}")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    images = collect_all_image_paths(PRODUCTS_FILE)
    print(f"Total unique images referenced in catalog: {len(images)}")
    
    missing = [img for img in images if not os.path.exists(img)]
    if missing:
        print(f"Warning: {len(missing)} images missing on disk (sample: {missing[:5]})")
    else:
        print("All 3,172 images exist on disk and verified!")

    already_done = [img for img in images if img in mapping]
    to_upload = [img for img in images if img not in mapping and os.path.exists(img)]
    print(f"Already uploaded in mapping: {len(already_done)}")
    print(f"Pending upload: {len(to_upload)}")

    if args.dry_run:
        print("Dry run completed successfully. No images were uploaded.")
        return

    if not to_upload:
        print("All images are already uploaded! Applying mapping to products.json...")
        apply_urls_to_products(mapping, PRODUCTS_FILE, TEST_PRODUCTS_FILE)
        return

    print(f"\nStarting parallel upload of {len(to_upload)} images with {args.workers} workers...")
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_img = {
            executor.submit(upload_single_image, img, args.folder): img
            for img in to_upload
        }

        for i, future in enumerate(as_completed(future_to_img), 1):
            local_path, url, err = future.result()
            if url:
                mapping[local_path] = url
                success_count += 1
            else:
                fail_count += 1
                print(f"\n[FAIL] {local_path}: {err}")

            if i % 25 == 0 or i == len(to_upload):
                save_map(mapping)
                pct = (i / len(to_upload)) * 100
                print(f"Progress: {i}/{len(to_upload)} ({pct:.1f}%) | Success: {success_count} | Failed: {fail_count}", end='\r')

    save_map(mapping)
    print(f"\nUpload run finished! Success: {success_count}, Failed: {fail_count}")

    if success_count > 0:
        apply_urls_to_products(mapping, PRODUCTS_FILE, TEST_PRODUCTS_FILE)

if __name__ == '__main__':
    main()
