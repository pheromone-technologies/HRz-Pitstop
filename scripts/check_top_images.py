import json
from PIL import Image
import os
import numpy as np

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

for p in products[0:20]:
    img = p.get('image')
    if img and os.path.exists(img):
        im = Image.open(img)
        arr = np.array(im)
        mode = im.mode
        has_alpha = mode in ('RGBA', 'LA') or (mode == 'P' and 'transparency' in im.info)
        print(f"{p.get('name')[:35]:35s} | {im.size} | mode={mode} | alpha={has_alpha} | corners={arr[0,0][:3].tolist() if len(arr.shape)==3 else 'gray'}")
