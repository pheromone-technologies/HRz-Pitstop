import os
import glob
from rembg import remove
from PIL import Image

def process_images():
    print("Starting background removal process...")
    image_dir = os.path.join(os.path.dirname(__file__), 'images', 'bikes')
    
    # Process all jpgs
    jpg_files = glob.glob(os.path.join(image_dir, '*.jpg'))
    
    total = len(jpg_files)
    for i, file_path in enumerate(jpg_files):
        print(f"Processing {i+1}/{total}: {os.path.basename(file_path)}")
        try:
            # We want to keep the original filename but change the extension to png
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            out_path = os.path.join(image_dir, base_name + '_transparent.png')
            
            # If already processed, skip
            if os.path.exists(out_path):
                continue
                
            with open(file_path, 'rb') as i_file:
                input_img = i_file.read()
                
            output_img = remove(input_img)
            
            with open(out_path, 'wb') as o_file:
                o_file.write(output_img)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    process_images()
