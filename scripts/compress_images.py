import os
from PIL import Image

# Constants
IMAGE_DIR = "docs/images/"
MAX_FILE_SIZE_KB = 500
TARGET_WIDTH = 1920

def compress_image(file_path):
    """Resizes and compresses an image to fit within MAX_FILE_SIZE_KB."""
    try:
        img = Image.open(file_path)
        
        # Convert to RGB if necessary (handles RGBA/PNG to JPEG conversion)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Resize if the image is larger than the target width
        if img.width > TARGET_WIDTH:
            ratio = TARGET_WIDTH / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((TARGET_WIDTH, new_height), Image.Resampling.LANCZOS)
        
        # Iteratively reduce quality until file size is under target
        quality = 85
        while quality > 10:
            img.save(file_path, "JPEG", quality=quality, optimize=True)
            if os.path.getsize(file_path) <= MAX_FILE_SIZE_KB * 1024:
                break
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
