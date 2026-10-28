import json
import openpyxl
from PIL import Image
import numpy as np

# 1. Update data/products.json
with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

before_count = len(products)
products = [p for p in products if p.get('id') != 'hrz-lcb-interceptor-650-thanos-crashguard-with-slider-1278']
print(f'Removed duplicate 1278: {before_count} -> {len(products)}')

swapped = []
for p in products:
    img1 = p.get('image', '')
    gallery = p.get('gallery', [])
    if len(gallery) > 1 and img1:
        try:
            im1 = Image.open(img1)
            im2 = Image.open(gallery[1])
            m1 = np.array(im1).mean()
            m2 = np.array(im2).mean()
            # If main image is dark/smoky/bike and second image is clean studio white background cutout
            if m1 < 210 and m2 > 235:
                p['image'] = gallery[1]
                gallery[1] = img1
                p['gallery'] = gallery
                swapped.append((p['id'], p['name'], img1, p['image']))
        except Exception:
            pass

print(f'Swapped {len(swapped)} products to clean white studio cutouts:')
for pid, name, old_img, new_img in swapped:
    print(f' - {name}: {old_img} -> {new_img}')

with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

# 2. Update Verified_Products_FINAL-1.xlsx
wb = openpyxl.load_workbook('Verified_Products_FINAL-1.xlsx')
ws = wb.active
headers = [cell.value for cell in ws[1]]
name_col = headers.index('Product Name') + 1
img_col = headers.index('Product Image Filename / URL') + 1
gallery_col = headers.index('Gallery Images') + 1

# Delete duplicate row for LCB INTERCEPTOR 650 THANOS CRASHGUARD WITH SLIDER
rows_to_delete = []
for row_idx in range(2, ws.max_row + 1):
    val = ws.cell(row=row_idx, column=name_col).value
    if val and val.strip() == 'LCB INTERCEPTOR 650 THANOS CRASHGUARD WITH SLIDER':
        rows_to_delete.append(row_idx)

for r_idx in reversed(rows_to_delete):
    ws.delete_rows(r_idx)
    print(f'Deleted duplicate row {r_idx} from Excel')

# Update swapped images in Excel
swapped_dict = {pid: (old_i, new_i) for pid, name, old_i, new_i in swapped}
# Also build by name
name_swap_dict = {name.lower().strip(): (old_i, new_i) for pid, name, old_i, new_i in swapped}

for row_idx in range(2, ws.max_row + 1):
    name_val = ws.cell(row=row_idx, column=name_col).value
    if name_val:
        key = name_val.lower().strip()
        if key in name_swap_dict:
            old_i, new_i = name_swap_dict[key]
            ws.cell(row=row_idx, column=img_col, value=new_i)
            # Also swap in gallery string
            gal_val = ws.cell(row=row_idx, column=gallery_col).value
            if gal_val:
                gal_imgs = [g.strip() for g in gal_val.split(',') if g.strip()]
                if len(gal_imgs) > 1 and gal_imgs[0] == old_i and gal_imgs[1] == new_i:
                    gal_imgs[0], gal_imgs[1] = gal_imgs[1], gal_imgs[0]
                    ws.cell(row=row_idx, column=gallery_col, value=', '.join(gal_imgs))

wb.save('Verified_Products_FINAL-1.xlsx')
print('Successfully updated Verified_Products_FINAL-1.xlsx!')
