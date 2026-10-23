"""Normalize generated device views onto consistent white PNG canvases."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps


VIEWS = ("front", "back", "left", "right", "top", "bottom")
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def _foreground_mask(image: Image.Image) -> Image.Image:
    """Return a conservative mask for visible pixels on a light background."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getextrema() != (255, 255):
        return alpha.point(lambda value: 255 if value > 12 else 0)

    rgb = rgba.convert("RGB")
    white = Image.new("RGB", rgb.size, (255, 255, 255))
    difference = ImageChops.difference(rgb, white).convert("L")
    mask = difference.point(lambda value: 255 if value > 10 else 0)
    return mask.filter(ImageFilter.MaxFilter(3))


def _trim_to_content(image: Image.Image) -> Image.Image:
    mask = _foreground_mask(image)
    bbox = mask.getbbox()
    if bbox is None:
        return image.convert("RGBA")

    return image.convert("RGBA").crop(bbox)


def normalize_image(image: Image.Image, canvas_size: int, occupancy: float) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    cropped = _trim_to_content(image)

    white = Image.new("RGBA", cropped.size, (255, 255, 255, 255))
    white.alpha_composite(cropped)

    inner_size = max(1, round(canvas_size * occupancy))
    fitted = ImageOps.contain(
        white,
        (inner_size, inner_size),
        method=Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
    x = (canvas_size - fitted.width) // 2
    y = (canvas_size - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))
    return canvas.convert("RGB")


def _find_view_file(input_dir: Path, view: str) -> Path | None:
    candidates = {path.stem.lower(): path for path in input_dir.iterdir() if path.is_file()}
    for extension in EXTENSIONS:
        candidate = candidates.get(view)
        if candidate and candidate.suffix.lower() == extension:
            return candidate
    return next(
        (path for path in input_dir.iterdir() if path.is_file() and path.stem.lower() == view),
        None,
    )


def _normalize_one(source: Path, destination: Path, canvas_size: int, occupancy: float) -> None:
    with Image.open(source) as image:
        result = normalize_image(image, canvas_size, occupancy)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, format="PNG", optimize=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-dir", type=Path, help="Directory containing named view images")
    group.add_argument("--input", type=Path, help="One source image to normalize")
    parser.add_argument("--view", choices=VIEWS, help="View name required with --input")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--canvas-size", type=int, default=2048)
    parser.add_argument("--occupancy", type=float, default=0.82)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.canvas_size < 256:
        print("--canvas-size must be at least 256", file=sys.stderr)
        return 2
    if not 0.1 <= args.occupancy <= 0.95:
        print("--occupancy must be between 0.1 and 0.95", file=sys.stderr)
        return 2

    if args.input is not None:
        if args.view is None:
            print("--view is required with --input", file=sys.stderr)
            return 2
        if not args.input.is_file():
            print(f"Input file not found: {args.input}", file=sys.stderr)
            return 2
        _normalize_one(
            args.input,
            args.output_dir / f"{args.view}.png",
            args.canvas_size,
            args.occupancy,
        )
        return 0

    if not args.input_dir.is_dir():
        print(f"Input directory not found: {args.input_dir}", file=sys.stderr)
        return 2

    missing = []
    processed = 0
    for view in VIEWS:
        source = _find_view_file(args.input_dir, view)
        if source is None:
            missing.append(view)
            continue
        _normalize_one(
            source,
            args.output_dir / f"{view}.png",
            args.canvas_size,
            args.occupancy,
        )
        processed += 1

    if missing:
        print(f"Normalized {processed} view(s); missing: {', '.join(missing)}", file=sys.stderr)
        return 1
    print(f"Normalized {processed} view(s) into {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
