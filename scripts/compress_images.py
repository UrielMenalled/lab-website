import os
from PIL import Image, ImageOps

# Constants
IMAGE_DIR = "docs/images/"
MAX_FILE_SIZE_KB = 500
TARGET_WIDTH = 1920

def compress_image(file_path):
    """Resizes and compresses an image to fit within MAX_FILE_SIZE_KB, strictly preserving rotation and aspect ratio."""
    try:
        with Image.open(file_path) as img:
            # 1. Fix rotation using EXIF data immediately upon opening
            img_fixed = ImageOps.exif_transpose(img)
            
            # 2. Convert to RGB if necessary (handles RGBA/PNG to JPEG conversion)
            if img_fixed.mode in ("RGBA", "P"):
                img_fixed = img_fixed.convert("RGB")
            
            # 3. Resize if the image is larger than the target width while maintaining aspect ratio
            w, h = img_fixed.size
            if w > TARGET_WIDTH:
                ratio = TARGET_WIDTH / float(w)
                new_h = int(float(h) * ratio)
                img_fixed = img_fixed.resize((TARGET_WIDTH, new_h), Image.Resampling.LANCZOS)
            
            # 4. Iteratively reduce quality until file size is under target
            quality = 85
            while quality > 10:
                # Save to a temporary file to verify size before replacing original
                tmp_path = file_path + ".tmp"
                img_fixed.save(tmp_path, "JPEG", quality=quality, optimize=True)
                
                if os.path.getsize(tmp_path) <= MAX_FILE_SIZE_KB * 1024:
                    os.replace(tmp_path, file_path)
                    break
                
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                quality -= 5
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def process_all_images():
    """Processes all compatible images in the target directory."""
    if not os.path.exists(IMAGE_DIR):
        print(f"Directory {IMAGE_DIR} not found.")
        return 0
        
    processed_count = 0
    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            file_path = os.path.join(IMAGE_DIR, filename)
            if compress_image(file_path):
                processed_count += 1
    return processed_count

if __name__ == "__main__":
    count = process_all_images()
    print(f"Successfully compressed {count} images in {IMAGE_DIR}")
