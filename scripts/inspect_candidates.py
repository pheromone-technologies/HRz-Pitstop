import os
from PIL import Image
import numpy as np

for f in sorted(os.listdir('scratch/image_candidates')):
    if not f.endswith(('.webp', '.jpg', '.png')): continue
    path = os.path.join('scratch/image_candidates', f)
    im = Image.open(path).convert('RGB')
    arr = np.array(im)
    corners = [arr[0,0], arr[0,-1], arr[-1,0], arr[-1,-1]]
    avg_corner = np.mean(corners, axis=0)
    print(f"{f}: size={im.size}, corner_rgb={[int(x) for x in avg_corner]}")
