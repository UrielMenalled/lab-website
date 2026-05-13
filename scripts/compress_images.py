import os
import re
from PIL import Image

# Constants
IMAGE_DIR = "docs/images/"
HTML_DIRS = ["docs/"]
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


def convert_to_webp(file_path):
    """Converts an image to WebP and saves it alongside the original.
    Only keeps the WebP if it is smaller than the original. Returns True if a WebP was saved."""
    stem, _ = os.path.splitext(file_path)
    webp_path = stem + ".webp"
    orig_size = os.path.getsize(file_path)

    try:
        with Image.open(file_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(webp_path, "WEBP", quality=82, method=6)

        if os.path.getsize(webp_path) < orig_size:
            print(f"  WebP saved ({os.path.getsize(webp_path) // 1024} KB vs {orig_size // 1024} KB): {webp_path}")
            return True
        else:
            os.remove(webp_path)
            print(f"  WebP skipped (not smaller than original): {file_path}")
            return False
    except Exception as e:
        print(f"Error converting {file_path} to WebP: {e}")
        if os.path.exists(webp_path):
            os.remove(webp_path)
        return False


def update_html_picture_tags(html_dirs, image_dir):
    """Wraps <img> tags in <picture> elements for images that have a WebP counterpart.
    Skips images without a .webp file, and skips <img> tags already inside a <picture>."""
    webp_stems = {
        os.path.splitext(f)[0]
        for f in os.listdir(image_dir)
        if f.endswith(".webp")
    }

    for directory in html_dirs:
        for fname in os.listdir(directory):
            if not fname.endswith(".html"):
                continue
            html_path = os.path.join(directory, fname)
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()

            original = content

            def replace_img(match):
                full_tag = match.group(0)
                src_match = re.search(r'src=["\']([^"\']+)["\']', full_tag)
                if not src_match:
                    return full_tag

                src = src_match.group(1)
                # Only process images that live in the images/ folder
                if not src.startswith("images/"):
                    return full_tag

                stem = os.path.splitext(os.path.basename(src))[0]
                if stem not in webp_stems:
                    return full_tag

                webp_src = f"images/{stem}.webp"

                # Add loading and decoding attributes if missing
                if "loading=" not in full_tag:
                    full_tag = full_tag.rstrip(">").rstrip("/") + ' loading="lazy">'
                if "decoding=" not in full_tag:
                    full_tag = full_tag.rstrip(">").rstrip("/") + ' decoding="async">'

                # Determine indentation of the <img> line
                pos = match.start()
                line_start = content.rfind("\n", 0, pos) + 1
                indent = " " * (pos - line_start)

                return (
                    f"<picture>\n"
                    f"{indent}  <source srcset=\"{webp_src}\" type=\"image/webp\">\n"
                    f"{indent}  {full_tag}\n"
                    f"{indent}</picture>"
                )

            # Only replace <img> tags NOT already inside a <picture>
            # Strategy: replace all, then clean up double-wrapped ones
            # Use a negative lookbehind via a two-pass approach:
            # Pass 1 — replace bare <img> tags (not preceded by <source ...>)
            img_pattern = re.compile(r'<img\b[^>]*>', re.IGNORECASE)

            # Split on <picture>...</picture> blocks to avoid touching existing ones
            picture_pattern = re.compile(r'<picture>.*?</picture>', re.DOTALL | re.IGNORECASE)
            parts = picture_pattern.split(content)
            picture_blocks = picture_pattern.findall(content)

            new_parts = [img_pattern.sub(replace_img, part) for part in parts]

            # Reassemble
            result = ""
            for i, part in enumerate(new_parts):
                result += part
                if i < len(picture_blocks):
                    result += picture_blocks[i]
            content = result

            if content != original:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Updated <picture> tags in {html_path}")


def process_all_images():
    """Processes all compatible images in the target directory."""
    if not os.path.exists(IMAGE_DIR):
        print(f"Directory {IMAGE_DIR} not found.")
        return 0

    processed_count = 0
    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            file_path = os.path.join(IMAGE_DIR, filename)
            print(f"Processing {filename}...")
            if compress_image(file_path):
                convert_to_webp(file_path)
                processed_count += 1

    return processed_count


if __name__ == "__main__":
    count = process_all_images()
    print(f"\nSuccessfully compressed {count} images in {IMAGE_DIR}")
    update_html_picture_tags(HTML_DIRS, IMAGE_DIR)
    print("Done.")
