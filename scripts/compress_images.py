import os
from PIL import Image

# Constants
IMAGE_DIR = "docs/images/"
MAX_FILE_SIZE_KB = 500
TARGET_WIDTH = 1920

def compress_image(file_path):
    """Resizes and compresses an image to fit within MAX_FILE_SIZE_KB, preserving original orientation and aspect ratio."""
    try:
        with Image.open(file_path) as img:
            # Preserve original EXIF data (including orientation) to avoid rotation changes
            exif = img.info.get("exif", b"")

            # Convert to RGB if necessary (handles RGBA/PNG to JPEG conversion)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize based on the longest dimension to handle both portrait and landscape
            w, h = img.size
            if max(w, h) > TARGET_WIDTH:
                if w >= h:
                    new_w = TARGET_WIDTH
                    new_h = int(h * TARGET_WIDTH / w)
                else:
                    new_h = TARGET_WIDTH
                    new_w = int(w * TARGET_WIDTH / h)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Iteratively reduce quality until file size is under target
            quality = 85
            while quality > 10:
                tmp_path = file_path + ".tmp"
                img.save(tmp_path, "JPEG", quality=quality, optimize=True, exif=exif)

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
