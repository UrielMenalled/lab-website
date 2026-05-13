import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image, ImageOps


IMAGE_DIR = Path("docs/images")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MOBILE_SUFFIX = "-mobile"

DESKTOP_MAX_DIMENSION = 1920
DESKTOP_MAX_FILE_SIZE_KB = 500
MOBILE_MAX_DIMENSION = 900
MOBILE_MAX_FILE_SIZE_KB = 250

JPEG_QUALITY_START = 85
JPEG_QUALITY_MIN = 35
JPEG_QUALITY_STEP = 5


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def is_mobile_variant(path: Path) -> bool:
    return path.stem.endswith(MOBILE_SUFFIX)


def resized_dimensions(width: int, height: int, max_dimension: int) -> tuple[int, int]:
    longest_side = max(width, height)
    if longest_side <= max_dimension:
        return width, height

    scale = max_dimension / longest_side
    return int(width * scale), int(height * scale)


def save_variant(source_path: Path, output_path: Path, max_dimension: int, max_file_size_kb: int) -> bool:
    try:
        with Image.open(source_path) as source_image:
            image = ImageOps.exif_transpose(source_image)
            exif = source_image.info.get("exif", b"")
            output_format = "PNG" if output_path.suffix.lower() == ".png" else "JPEG"

            if output_format == "JPEG" and image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            new_width, new_height = resized_dimensions(*image.size, max_dimension)
            if (new_width, new_height) != image.size:
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            output_path.parent.mkdir(parents=True, exist_ok=True)

            if output_format == "PNG":
                with NamedTemporaryFile(dir=output_path.parent, suffix=output_path.suffix, delete=False) as temp_file:
                    temp_path = Path(temp_file.name)

                image.save(temp_path, format="PNG", optimize=True)
                temp_path.replace(output_path)
                return True

            for quality in range(JPEG_QUALITY_START, JPEG_QUALITY_MIN - 1, -JPEG_QUALITY_STEP):
                with NamedTemporaryFile(dir=output_path.parent, suffix=output_path.suffix, delete=False) as temp_file:
                    temp_path = Path(temp_file.name)

                image.save(
                    temp_path,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                    exif=exif,
                )

                if temp_path.stat().st_size <= max_file_size_kb * 1024 or quality == JPEG_QUALITY_MIN:
                    temp_path.replace(output_path)
                    return True

                temp_path.unlink(missing_ok=True)

        return False
    except Exception as exc:
        print(f"Error processing {source_path}: {exc}")
        return False


def resolve_source_images(image_paths: list[str] | None) -> list[Path]:
    if image_paths:
        resolved_paths = []
        for image_path in image_paths:
            path = Path(image_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            resolved_paths.append(path)
        candidate_paths = resolved_paths
    else:
        candidate_paths = sorted(IMAGE_DIR.iterdir())

    return [
        path
        for path in candidate_paths
        if path.is_file() and is_supported_image(path) and not is_mobile_variant(path)
    ]


def process_images(image_paths: list[str] | None = None) -> tuple[int, int]:
    if not IMAGE_DIR.exists():
        print(f"Directory {IMAGE_DIR} not found.")
        return 0, 0

    source_images = resolve_source_images(image_paths)
    optimized_originals = 0
    generated_mobile_variants = 0

    for source_path in source_images:
        mobile_path = source_path.with_name(f"{source_path.stem}{MOBILE_SUFFIX}{source_path.suffix}")

        optimized_original = save_variant(
            source_path=source_path,
            output_path=source_path,
            max_dimension=DESKTOP_MAX_DIMENSION,
            max_file_size_kb=DESKTOP_MAX_FILE_SIZE_KB,
        )
        generated_mobile = save_variant(
            source_path=source_path,
            output_path=mobile_path,
            max_dimension=MOBILE_MAX_DIMENSION,
            max_file_size_kb=MOBILE_MAX_FILE_SIZE_KB,
        )

        if optimized_original:
            optimized_originals += 1
        if generated_mobile:
            generated_mobile_variants += 1

    return optimized_originals, generated_mobile_variants


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optimize images and generate mobile variants.",
    )
    parser.add_argument(
        "images",
        nargs="*",
        help="Optional list of source image paths to process.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    optimized_originals, generated_mobile_variants = process_images(args.images)
    print(
        "Optimized "
        f"{optimized_originals} original images and generated "
        f"{generated_mobile_variants} mobile variants in {IMAGE_DIR}",
    )
