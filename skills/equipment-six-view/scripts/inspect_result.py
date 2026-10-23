"""Inspect six-view PNG deliverables for measurable image-quality failures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops


VIEWS = ("front", "back", "left", "right", "top", "bottom")
COMPOSITE = "six-view-composite.png"


def _border_fraction(image: Image.Image, border: int = 24) -> float:
    rgb = image.convert("RGB")
    width, height = rgb.size
    border = max(1, min(border, width // 4, height // 4))
    pixels = []
    pixels.extend(rgb.crop((0, 0, width, border)).getdata())
    pixels.extend(rgb.crop((0, height - border, width, height)).getdata())
    pixels.extend(rgb.crop((0, border, border, height - border)).getdata())
    pixels.extend(rgb.crop((width - border, border, width, height - border)).getdata())
    nonwhite = sum(1 for red, green, blue in pixels if min(red, green, blue) < 238)
    return nonwhite / max(1, len(pixels))


def _content_ratio(image: Image.Image) -> float:
    rgb = image.convert("RGB")
    white = Image.new("RGB", rgb.size, (255, 255, 255))
    diff = ImageChops.difference(rgb, white).convert("L")
    nonwhite = sum(1 for value in diff.getdata() if value > 10)
    return nonwhite / max(1, rgb.width * rgb.height)


def _inspect_file(path: Path, minimum_size: int) -> dict:
    result = {"path": str(path), "status": "pass", "errors": [], "warnings": []}
    if not path.is_file():
        result["status"] = "error"
        result["errors"].append("file_missing")
        return result

    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            result["size"] = [width, height]
            if width < minimum_size or height < minimum_size:
                result["status"] = "error"
                result["errors"].append("image_too_small")
            if image.format != "PNG":
                result["warnings"].append("not_png")
            border_fraction = _border_fraction(image)
            result["border_nonwhite_fraction"] = round(border_fraction, 6)
            if border_fraction > 0.08:
                result["status"] = "error"
                result["errors"].append("content_touches_or_contaminates_border")
            content_ratio = _content_ratio(image)
            result["content_ratio"] = round(content_ratio, 6)
            if content_ratio < 0.001:
                result["status"] = "error"
                result["errors"].append("blank_or_nearly_blank")
            elif content_ratio > 0.92:
                result["warnings"].append("very_little_white_margin")
    except (OSError, ValueError) as error:
        result["status"] = "error"
        result["errors"].append(f"unreadable_image: {error}")
    return result


def inspect(input_dir: Path, minimum_size: int, expected_composite_size: int) -> dict:
    files = {view: _inspect_file(input_dir / f"{view}.png", minimum_size) for view in VIEWS}
    composite = _inspect_file(input_dir / COMPOSITE, expected_composite_size)
    errors = sum(len(item["errors"]) for item in files.values()) + len(composite["errors"])
    warnings = sum(len(item["warnings"]) for item in files.values()) + len(composite["warnings"])
    return {
        "status": "fail" if errors else "pass",
        "semantic_review_required": True,
        "summary": {"errors": errors, "warnings": warnings},
        "views": files,
        "composite": composite,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--minimum-size", type=int, default=1024)
    parser.add_argument("--composite-size", type=int, default=4096)
    parser.add_argument("--fail-on-warning", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if not args.input_dir.is_dir():
        print(f"Input directory not found: {args.input_dir}", file=sys.stderr)
        return 2
    report = inspect(args.input_dir, args.minimum_size, args.composite_size)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] == "fail":
        return 1
    if args.fail_on_warning and report["summary"]["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
