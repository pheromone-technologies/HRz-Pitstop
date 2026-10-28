import json
import os
import sys
from PIL import Image, ImageStat

sys.stdout.reconfigure(encoding='utf-8')

with open('data/products.json', encoding='utf-8') as f:
    products = json.load(f)

print(f"Total products to audit: {len(products)}")

results = {
    "missing_images": [],
    "tiny_files": [],          # < 4KB (often corrupted or empty)
    "mostly_blank_or_white": [], # > 96% white pixels or stddev < 5
    "mostly_transparent_cutout": [], # product area < 5% of canvas
    "distorted_aspect": [],    # ratio > 2.2 or < 0.45
    "all_black_or_dark": [],   # mean luminance < 15
    "suspicious_rembg_holes": []
}

for idx, p in enumerate(products):
    img_path = p.get('image', '')
    p_id = p.get('id', f'prod_{idx}')
    p_name = p.get('name', 'Unknown')
    cat = p.get('category', 'Uncategorized')

    if not img_path:
        results["missing_images"].append({"id": p_id, "name": p_name, "category": cat, "reason": "No image path in record"})
        continue

    norm_path = img_path.replace('/', os.sep)
    if not os.path.exists(norm_path):
        results["missing_images"].append({"id": p_id, "name": p_name, "category": cat, "path": img_path, "reason": "File does not exist on disk"})
        continue

    file_size = os.path.getsize(norm_path)
    if file_size < 3500:
        results["tiny_files"].append({"id": p_id, "name": p_name, "category": cat, "path": img_path, "size_bytes": file_size})

    try:
        with Image.open(norm_path) as im:
            w, h = im.size
            ratio = w / float(h)
            if ratio > 2.5 or ratio < 0.4:
                results["distorted_aspect"].append({"id": p_id, "name": p_name, "category": cat, "path": img_path, "dims": f"{w}x{h}", "ratio": round(ratio, 2)})

            # Analyze pixel contents
            rgb_im = im.convert('RGB')
            stat = ImageStat.Stat(rgb_im)
            mean_lum = sum(stat.mean) / 3.0
            std_dev = sum(stat.stddev) / 3.0

            if mean_lum > 250 and std_dev < 10:
                results["mostly_blank_or_white"].append({"id": p_id, "name": p_name, "category": cat, "path": img_path, "mean_lum": round(mean_lum, 1), "std_dev": round(std_dev, 1)})
            elif mean_lum < 20 and std_dev < 15:
                results["all_black_or_dark"].append({"id": p_id, "name": p_name, "category": cat, "path": img_path, "mean_lum": round(mean_lum, 1), "std_dev": round(std_dev, 1)})

            # Check coverage of product (non-white pixels)
            # White canvas is rgb > (248, 248, 248)
            # Sample thumbnail for speed
            thumb = rgb_im.resize((100, 100))
            pixels = list(thumb.getdata())
            # count non-white pixels
            non_white = sum(1 for (r, g, b) in pixels if not (r > 240 and g > 240 and b > 240))
            coverage = non_white / float(len(pixels))

            if coverage < 0.04:  # less than 4% of image is the product -> rembg cut out the whole thing!
                results["mostly_transparent_cutout"].append({
                    "id": p_id,
                    "name": p_name,
                    "category": cat,
                    "path": img_path,
                    "product_coverage_pct": round(coverage * 100, 1),
                    "reason": "Rembg removed product leaving nearly empty white canvas"
                })

    except Exception as e:
        results["tiny_files"].append({"id": p_id, "name": p_name, "category": cat, "path": img_path, "error": str(e)})

    if (idx + 1) % 400 == 0:
        print(f"Processed {idx + 1}/{len(products)}...")

with open('scratch/image_audit_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n--- IMAGE AUDIT SUMMARY ---")
print(f"Missing image files: {len(results['missing_images'])}")
print(f"Tiny/corrupted files (<3.5KB): {len(results['tiny_files'])}")
print(f"Mostly blank/pure white: {len(results['mostly_blank_or_white'])}")
print(f"Cutout wiped out (product < 4% coverage): {len(results['mostly_transparent_cutout'])}")
print(f"All black / dark blob: {len(results['all_black_or_dark'])}")
print(f"Distorted aspect ratio: {len(results['distorted_aspect'])}")
