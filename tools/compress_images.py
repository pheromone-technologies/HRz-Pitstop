import os
from PIL import Image

image_dir = 'images'
for filename in os.listdir(image_dir):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        file_path = os.path.join(image_dir, filename)
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB for JPEG if needed, but WebP supports RGBA natively!
                webp_path = os.path.splitext(file_path)[0] + '.webp'
                img.save(webp_path, 'webp', quality=85, method=6)
            
            # Delete original file
            os.remove(file_path)
            print(f"Compressed {filename} to WebP")
        except Exception as e:
            print(f"Error compressing {filename}: {e}")
