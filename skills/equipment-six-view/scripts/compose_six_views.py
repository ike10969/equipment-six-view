"""Compose normalized device views into standalone files and one reference sheet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter


VIEWS = ("front", "back", "left", "right", "top", "bottom")
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
LABELS = {
    "front": "正面 / FRONT",
    "back": "背面 / BACK",
    "left": "左侧面 / LEFT",
    "right": "右侧面 / RIGHT",
    "top": "俯视图 / TOP",
    "bottom": "底视图 / BOTTOM",
}


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _find_view_file(input_dir: Path, view: str) -> Path | None:
    for extension in EXTENSIONS:
        candidate = input_dir / f"{view}{extension}"
        if candidate.is_file():
            return candidate
    return None


def _content_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getextrema() != (255, 255):
        return alpha.point(lambda value: 255 if value > 12 else 0).getbbox()

    rgb = rgba.convert("RGB")
    white = Image.new("RGB", rgb.size, (255, 255, 255))
    difference = ImageChops.difference(rgb, white).convert("L")
    return difference.point(lambda value: 255 if value > 10 else 0).filter(ImageFilter.MaxFilter(3)).getbbox()


def _paste_object(canvas: Image.Image, source: Image.Image, slot: tuple[int, int, int, int]) -> None:
    left, top, width, height = slot
    rgba = source.convert("RGBA")
    bbox = _content_bbox(rgba)
    if bbox is not None:
        rgba = rgba.crop(bbox)

    fitted = rgba.copy()
    fitted.thumbnail((max(1, width - 40), max(1, height - 80)), Image.Resampling.LANCZOS)
    x = left + (width - fitted.width) // 2
    y = top + (height - fitted.height) // 2 - 18
    canvas.alpha_composite(fitted, (x, y))


def _draw_label(canvas: Image.Image, view: str, slot: tuple[int, int, int, int], font: ImageFont.ImageFont) -> None:
    left, top, width, height = slot
    draw = ImageDraw.Draw(canvas)
    label = LABELS[view]
    box = draw.textbbox((0, 0), label, font=font)
    x = left + (width - (box[2] - box[0])) // 2
    y = top + height - 42
    draw.text((x, y), label, fill=(92, 92, 92, 255), font=font)


def compose(input_dir: Path, output_dir: Path, size: int, labels: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    images: dict[str, Image.Image] = {}
    missing = []
    for view in VIEWS:
        source = _find_view_file(input_dir, view)
        if source is None:
            missing.append(view)
            continue
        with Image.open(source) as image:
            images[view] = image.convert("RGBA")

    if missing:
        raise FileNotFoundError(f"Missing normalized views: {', '.join(missing)}")

    standalone_size = max(256, size // 2)
    for view, image in images.items():
        standalone = Image.new("RGBA", (standalone_size, standalone_size), (255, 255, 255, 255))
        _paste_object(standalone, image, (0, 0, standalone_size, standalone_size))
        standalone.convert("RGB").save(output_dir / f"{view}.png", format="PNG", optimize=True)

    composite = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    margin = round(size * 0.025)
    slot_width = round(size * 0.215)
    slot_height = round(size * 0.39)
    center_y = round(size * 0.30)
    horizontal_gap = round(size * 0.017)
    xs = [
        margin,
        margin + slot_width + horizontal_gap,
        margin + 2 * (slot_width + horizontal_gap),
        margin + 3 * (slot_width + horizontal_gap),
    ]
    slots = {
        "left": (xs[0], center_y, slot_width, slot_height),
        "front": (xs[1], center_y, slot_width, slot_height),
        "right": (xs[2], center_y, slot_width, slot_height),
        "back": (xs[3], center_y, slot_width, slot_height),
        "top": (xs[1], margin, slot_width, round(size * 0.18)),
        "bottom": (xs[1], round(size * 0.75), slot_width, round(size * 0.20)),
    }
    font = _find_font(max(18, round(size * 0.014)))
    for view in VIEWS:
        _paste_object(composite, images[view], slots[view])
        if labels:
            _draw_label(composite, view, slots[view], font)

    composite.convert("RGB").save(output_dir / "six-view-composite.png", format="PNG", optimize=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--size", type=int, default=4096)
    parser.add_argument("--no-labels", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.size < 1024:
        print("--size must be at least 1024", file=sys.stderr)
        return 2
    if not args.input_dir.is_dir():
        print(f"Input directory not found: {args.input_dir}", file=sys.stderr)
        return 2
    try:
        compose(args.input_dir, args.output_dir, args.size, not args.no_labels)
    except (FileNotFoundError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"Wrote six-view deliverables into {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
