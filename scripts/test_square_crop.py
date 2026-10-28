import os
from PIL import Image
import numpy as np

def make_clean_square_product_image(src_path, dst_path, target_size=1080):
    im = Image.open(src_path).convert('RGB')
    arr = np.array(im)
    h, w, _ = arr.shape
    
    # Estimate background color from the 4 corners
    corners = np.vstack([arr[:20, :20], arr[:20, -20:], arr[-20:, :20], arr[-20:, -20:]])
    bg_color = np.median(corners.reshape(-1, 3), axis=0).astype(int)
    
    # Calculate distance from background color
    diff = np.sqrt(np.sum((arr.astype(int) - bg_color)**2, axis=2))
    content_mask = diff > 25
    
    if np.any(content_mask):
        ys, xs = np.where(content_mask)
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        
        # Crop to content box
        content = im.crop((xmin, ymin, xmax + 1, ymax + 1))
        cw, ch = content.size
        
        # Add 12% margin around the max dimension
        max_dim = max(cw, ch)
        pad = int(max_dim * 0.12)
        side = max_dim + pad * 2
        
        # If bg_color is nearly white (>230), use pure white (255, 255, 255)
        if np.mean(bg_color) > 220:
            canvas_bg = (255, 255, 255)
        else:
            canvas_bg = tuple(int(c) for c in bg_color)
            
        square = Image.new('RGB', (side, side), canvas_bg)
        offset_x = (side - cw) // 2
        offset_y = (side - ch) // 2
        square.paste(content, (offset_x, offset_y))
        
        # Resize to target_size
        final_im = square.resize((target_size, target_size), Image.Resampling.LANCZOS)
    else:
        # Fallback to direct square resize with padding
        max_dim = max(w, h)
        square = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
        square.paste(im, ((max_dim - w) // 2, (max_dim - h) // 2))
        final_im = square.resize((target_size, target_size), Image.Resampling.LANCZOS)
        
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    final_im.save(dst_path, 'WEBP', quality=92)
    print(f"Created {dst_path} (1080x1080) from {src_path}")

# Test on candidate files
os.makedirs('scratch/test_squares', exist_ok=True)
tests = [
    ('scratch/image_candidates/rtx_bp_silver_1.jpg', 'scratch/test_squares/rtx_bp_silver.webp'),
    ('scratch/image_candidates/rtx_bp_black_1.webp', 'scratch/test_squares/rtx_bp_black.webp'),
    ('scratch/image_candidates/rtx_rad_black_2.jpg', 'scratch/test_squares/rtx_rad_black.webp'),
    ('scratch/image_candidates/rtx_rad_silver_2.jpg', 'scratch/test_squares/rtx_rad_silver.webp'),
    ('scratch/image_candidates/vstrom_cg_8.webp', 'scratch/test_squares/vstrom_cg.webp'),
    ('scratch/image_candidates/vstrom_bp_2.webp', 'scratch/test_squares/vstrom_bp.webp'),
    ('scratch/image_candidates/xpulse_cosmic_2.jpg', 'scratch/test_squares/xpulse_cosmic.webp'),
    ('scratch/image_candidates/xpulse_hl_2.webp', 'scratch/test_squares/xpulse_hl.webp'),
]

for src, dst in tests:
    make_clean_square_product_image(src, dst)
