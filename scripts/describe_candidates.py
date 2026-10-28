import os
from PIL import Image
import numpy as np

def describe_image(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    arr = np.array(im)
    # find non-background bounding box
    # assume background is corner color
    corner = arr[0, 0].astype(int)
    diff = np.sqrt(np.sum((arr.astype(int) - corner)**2, axis=2))
    content_mask = diff > 30
    
    if np.any(content_mask):
        ys, xs = np.where(content_mask)
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        cw, ch = xmax - xmin, ymax - ymin
        coverage = np.mean(content_mask) * 100
        return f"{w}x{h}, content box: [{xmin},{ymin} to {xmax},{ymax}] ({cw}x{ch}), cov={coverage:.1f}%"
    return f"{w}x{h}, no content detected"

for f in sorted(os.listdir('scratch/image_candidates')):
    if not f.endswith(('.webp', '.jpg', '.png')): continue
    path = os.path.join('scratch/image_candidates', f)
    print(f"{f:20s}: {describe_image(path)}")
